"""Backend-only OpenAI RAG workflow with a durable SQLite conversation trace."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
from typing import Any
from uuid import uuid4

from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError

from config import get_openai_api_key, get_openai_model
from database import DATABASE_PATH, get_connection


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "hotel-assistant.md"
PROMPT_VERSION = "hotel-assistant-v1"
ALLOWED_TABLES = {"saved_hotels", "saved_hotel_zips", "demo_hotel_nights"}
MAX_ROWS = 10
MAX_HISTORY_MESSAGES = 8
_hotel_assistant_prompt = ""


class ChatConfigurationError(Exception):
    """Raised when the backend-only OpenAI key is unavailable."""


class ChatProviderError(Exception):
    """Raised for a sanitized OpenAI request failure."""


class ChatQueryRejectedError(Exception):
    """Raised when the model's SQL is not a permitted local read query."""


def initialize_hotel_assistant_prompt() -> None:
    """Load the versioned RAG context during backend startup."""
    global _hotel_assistant_prompt
    try:
        prompt = PROMPT_PATH.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise RuntimeError("The hotel assistant prompt could not be loaded.") from error
    if not prompt:
        raise RuntimeError("The hotel assistant prompt is empty.")
    _hotel_assistant_prompt = prompt


def _prompt() -> str:
    if not _hotel_assistant_prompt:
        initialize_hotel_assistant_prompt()
    return _hotel_assistant_prompt


def _record_message(
    conversation_id: str,
    role: str,
    stage: str,
    content: str,
    prompt_version: str | None = None,
) -> None:
    """Persist one auditable conversation or retrieval step."""
    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO conversation_messages (
                conversation_id, created_at, role, stage, content, prompt_version
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                role,
                stage,
                content,
                prompt_version,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def get_conversation_trace(conversation_id: str) -> list[dict]:
    """Return the saved, timestamped trace for one conversation."""
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT message_id, conversation_id, created_at, role, stage, content,
                   prompt_version
            FROM conversation_messages
            WHERE conversation_id = ?
            ORDER BY message_id
            """,
            (conversation_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def _conversation_messages_for_model(conversation_id: str) -> list[dict[str, str]]:
    """Keep prior user questions and completed assistant answers as context."""
    trace = get_conversation_trace(conversation_id)
    history = [
        {"role": row["role"], "content": row["content"]}
        for row in trace
        if (row["role"] == "user" and row["stage"] == "user_question")
        or (row["role"] == "assistant" and row["stage"] == "final_answer")
    ]
    return history[-MAX_HISTORY_MESSAGES:]


def _proposal_prompt(conversation_id: str) -> list[dict[str, str]]:
    instructions = (
        f"{_prompt()}\n\n"
        "For this first step, propose the SQL and parameters only. "
        "Follow the SQL proposal rules exactly."
    )
    return [{"role": "system", "content": instructions}, *_conversation_messages_for_model(conversation_id)]


def _answer_prompt(question: str, records: list[dict]) -> list[dict[str, str]]:
    evidence = json.dumps(records, ensure_ascii=False)
    return [
        {
            "role": "system",
            "content": (
                f"{_prompt()}\n\n"
                "This is the second step. Answer the original question only from the "
                "retrieved SQLite rows below. Explain empty or insufficient results "
                "instead of guessing. State that rates and rooms are simulated course data."
            ),
        },
        {
            "role": "user",
            "content": f"Original question: {question}\n\nRetrieved rows: {evidence}",
        },
    ]


def _request_chat_completion(
    messages: list[dict[str, str]], max_tokens: int, expect_json: bool
) -> str:
    """Make one credential-safe server-side OpenAI Chat Completions request."""
    api_key = get_openai_api_key()
    if not api_key:
        raise ChatConfigurationError
    request_options: dict[str, Any] = {
        "model": get_openai_model(),
        "messages": messages,
        "max_completion_tokens": max_tokens,
    }
    if expect_json:
        request_options["response_format"] = {"type": "json_object"}
    try:
        response = OpenAI(api_key=api_key).chat.completions.create(**request_options)
        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise ValueError("No assistant content")
        return content.strip()
    except (APIConnectionError, APIError, APITimeoutError, RateLimitError, ValueError, IndexError) as error:
        raise ChatProviderError from error


def request_chat_completion(
    messages: list[dict[str, str]], max_tokens: int, expect_json: bool = False
) -> str:
    """Single testable entry point for the backend-only OpenAI request."""
    return _request_chat_completion(messages, max_tokens, expect_json)


def _parse_sql_proposal(content: str) -> tuple[str, list[Any]]:
    """Parse JSON-only model output without accepting extra instructions."""
    candidate = content.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.I)
    try:
        proposal = json.loads(candidate)
    except json.JSONDecodeError as error:
        raise ChatQueryRejectedError("The assistant did not return a valid SQL proposal.") from error
    if not isinstance(proposal, dict):
        raise ChatQueryRejectedError("The assistant proposal has an invalid shape.")
    sql = proposal.get("sql")
    parameters = proposal.get("parameters")
    if not isinstance(sql, str) or not isinstance(parameters, list):
        raise ChatQueryRejectedError("The assistant proposal is missing SQL or parameters.")
    return sql, parameters


def validate_sql(sql: str, parameters: list[Any]) -> tuple[str, tuple[Any, ...]]:
    """Allow one bounded SELECT over approved saved-hotel tables only."""
    normalized = " ".join(sql.strip().split())
    lowered = normalized.lower()
    if not normalized or len(normalized) > 2200 or not lowered.startswith("select "):
        raise ChatQueryRejectedError("Only one local SELECT query is allowed.")
    forbidden = r"\b(insert|update|delete|drop|alter|create|replace|pragma|attach|detach|vacuum|reindex|analyze|trigger|transaction|begin|commit|rollback)\b"
    if ";" in normalized or "--" in normalized or "/*" in normalized or re.search(forbidden, lowered):
        raise ChatQueryRejectedError("The proposed query contains a disallowed operation.")
    table_names = re.findall(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)", lowered)
    if not table_names or any(table not in ALLOWED_TABLES for table in table_names):
        raise ChatQueryRejectedError("The proposed query may use only approved saved-hotel tables.")
    limit_match = re.search(r"\blimit\s+([0-9]+)\s*$", lowered)
    if limit_match is None or int(limit_match.group(1)) > MAX_ROWS:
        raise ChatQueryRejectedError("The proposed query must use LIMIT 10 or less.")
    if normalized.count("?") != len(parameters) or len(parameters) > 12:
        raise ChatQueryRejectedError("The proposed query has invalid parameters.")
    if any(not isinstance(value, (str, int, float)) or isinstance(value, bool) for value in parameters):
        raise ChatQueryRejectedError("The proposed query has unsupported parameter values.")
    return normalized, tuple(parameters)


def execute_readonly_query(sql: str, parameters: tuple[Any, ...]) -> list[dict]:
    """Run a validated query through a read-only, bounded SQLite connection."""
    database_uri = f"{DATABASE_PATH.resolve().as_uri()}?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.set_progress_handler(lambda: 1, 50_000)
    try:
        rows = connection.execute(sql, parameters).fetchall()
        if len(rows) > MAX_ROWS:
            raise ChatQueryRejectedError("The proposed query returned too many rows.")
        return [dict(row) for row in rows]
    except sqlite3.DatabaseError as error:
        raise ChatQueryRejectedError("The proposed query could not be run safely.") from error
    finally:
        connection.close()


def _display_messages(trace: list[dict]) -> list[dict]:
    """Return the user/answer conversation that the Vue interface displays."""
    return [
        {
            "message_id": row["message_id"],
            "created_at": row["created_at"],
            "role": row["role"],
            "content": row["content"],
        }
        for row in trace
        if (row["role"] == "user" and row["stage"] == "user_question")
        or (row["role"] == "assistant" and row["stage"] == "final_answer")
    ]


def ask_hotel_assistant(question: str, conversation_id: str | None = None) -> dict:
    """Run question → SQL proposal → checked retrieval → grounded answer and save it."""
    cleaned_question = question.strip()
    if len(cleaned_question) < 3:
        raise ChatQueryRejectedError("Enter a more specific hotel question.")
    active_conversation_id = conversation_id or f"hotel-{uuid4().hex}"
    _record_message(active_conversation_id, "user", "user_question", cleaned_question)
    try:
        proposal_content = request_chat_completion(
            _proposal_prompt(active_conversation_id), 550, expect_json=True
        )
        _record_message(
            active_conversation_id,
            "assistant",
            "proposed_sql",
            proposal_content,
            PROMPT_VERSION,
        )
        proposed_sql, proposed_parameters = _parse_sql_proposal(proposal_content)
        safe_sql, safe_parameters = validate_sql(proposed_sql, proposed_parameters)
        _record_message(
            active_conversation_id,
            "tool",
            "executed_sql",
            json.dumps({"sql": safe_sql, "parameters": safe_parameters}),
            PROMPT_VERSION,
        )
        records = execute_readonly_query(safe_sql, safe_parameters)
        _record_message(
            active_conversation_id,
            "tool",
            "retrieval_result",
            json.dumps(records, ensure_ascii=False),
            PROMPT_VERSION,
        )
        answer = request_chat_completion(_answer_prompt(cleaned_question, records), 500)
        _record_message(active_conversation_id, "assistant", "final_answer", answer, PROMPT_VERSION)
    except ChatQueryRejectedError as error:
        _record_message(active_conversation_id, "tool", "query_rejected", str(error), PROMPT_VERSION)
        raise
    except (ChatConfigurationError, ChatProviderError) as error:
        _record_message(active_conversation_id, "tool", "provider_error", type(error).__name__, PROMPT_VERSION)
        raise

    trace = get_conversation_trace(active_conversation_id)
    return {
        "conversation_id": active_conversation_id,
        "question": cleaned_question,
        "proposed_sql": safe_sql,
        "parameters": list(safe_parameters),
        "records": records,
        "answer": answer[:3000],
        "model": get_openai_model(),
        "rates_and_availability_are_simulated": True,
        "conversation": _display_messages(trace),
    }
