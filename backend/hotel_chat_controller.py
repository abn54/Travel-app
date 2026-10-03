"""Backend-only RAG workflow for questions about locally saved hotels."""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import get_openrouter_api_key
from database import DATABASE_PATH


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "nvidia/nemotron-3-ultra-550b-a55b-20260604:free"
OPENROUTER_FALLBACK_MODEL = "openrouter/free"
ALLOWED_TABLES = {"local_hotels", "demo_hotel_nights"}
MAX_ROWS = 10


class ChatConfigurationError(Exception):
    """Raised when the chatbot key is unavailable."""


class ChatProviderError(Exception):
    """Raised for a sanitized model-provider failure."""


class ChatQueryRejectedError(Exception):
    """Raised when the model's SQL is not a permitted local read query."""


def _proposal_prompt(question: str) -> list[dict[str, str]]:
    schema = """
You write SQLite SELECT statements for this local hotel course-data schema only.

local_hotels(
  place_id TEXT PRIMARY KEY, name TEXT, address TEXT, locality TEXT,
  latitude REAL, longitude REAL, search_postcode TEXT, saved_at TEXT
)
demo_hotel_nights(
  place_id TEXT REFERENCES local_hotels, stay_date TEXT in YYYY-MM-DD,
  nightly_rate_usd REAL, available_rooms INTEGER,
  PRIMARY KEY(place_id, stay_date)
)

Rules: return JSON only with exactly {"sql": string, "parameters": array}.
Write exactly one SELECT query. Use only the two listed tables and ? placeholders.
Never use INSERT, UPDATE, DELETE, PRAGMA, schema names, comments, or a semicolon.
Include LIMIT 10 or smaller. Rates and room counts are explicitly simulated course data.
When demo_hotel_nights is used, always select h.name, n.stay_date,
n.nightly_rate_usd, and n.available_rooms so the grounded answer can state the
date, simulated rate, and simulated availability accurately. Use h for
local_hotels and n for demo_hotel_nights. If there cannot be a match, still
return a safe SELECT against these tables that will produce no rows.
""".strip()
    return [
        {"role": "system", "content": schema},
        {"role": "user", "content": question},
    ]


def _answer_prompt(question: str, records: list[dict]) -> list[dict[str, str]]:
    evidence = json.dumps(records, ensure_ascii=False)
    return [
        {
            "role": "system",
            "content": (
                "Answer only from the supplied local SQLite records. Be concise and actionable. "
                "Clearly call nightly rates and room availability simulated course data. "
                "Do not invent hotels, dates, prices, availability, or booking confirmations. "
                "If records are empty or insufficient, say that clearly and suggest saving a nearby hotel or asking about available local data."
            ),
        },
        {
            "role": "user",
            "content": f"Original question: {question}\n\nRetrieved local records: {evidence}",
        },
    ]


def _request_chat_completion(
    messages: list[dict[str, str]], max_tokens: int, model: str, expect_json: bool
) -> str:
    """Make one backend-only, credential-safe OpenRouter request."""
    api_key = get_openrouter_api_key()
    if not api_key:
        raise ChatConfigurationError
    payload_object: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }
    if expect_json:
        payload_object["response_format"] = {"type": "json_object"}
        payload_object["reasoning"] = {"enabled": False}
    payload = json.dumps(payload_object).encode("utf-8")
    request = Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Expedia Lite",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=25) as response:
            response_body = json.loads(response.read().decode("utf-8"))
        content = response_body["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(
                item.get("text", "") for item in content if isinstance(item, dict)
            )
        if not isinstance(content, str) or not content.strip():
            raise ValueError("No assistant content")
        return content.strip()
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, json.JSONDecodeError) as error:
        raise ChatProviderError from error


def request_chat_completion(
    messages: list[dict[str, str]], max_tokens: int, expect_json: bool = False
) -> str:
    """Prefer Nemotron but retain a free OpenRouter fallback for availability."""
    try:
        return _request_chat_completion(
            messages, max_tokens, OPENROUTER_MODEL, expect_json
        )
    except ChatProviderError:
        return _request_chat_completion(
            messages, max_tokens, OPENROUTER_FALLBACK_MODEL, expect_json
        )


def _parse_sql_proposal(content: str) -> tuple[str, list[Any]]:
    """Parse JSON-only model output without accepting additional instructions."""
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
    """Allow one bounded SELECT over local tables and reject every write-like form."""
    normalized = " ".join(sql.strip().split())
    lowered = normalized.lower()
    if not normalized or len(normalized) > 1800 or not lowered.startswith("select "):
        raise ChatQueryRejectedError("Only one local SELECT query is allowed.")
    forbidden = r"\b(insert|update|delete|drop|alter|create|replace|pragma|attach|detach|vacuum|reindex|analyze|trigger|transaction|begin|commit|rollback)\b"
    if ";" in normalized or "--" in normalized or "/*" in normalized or re.search(forbidden, lowered):
        raise ChatQueryRejectedError("The proposed query contains a disallowed operation.")
    table_names = re.findall(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)", lowered)
    if not table_names or any(table not in ALLOWED_TABLES for table in table_names):
        raise ChatQueryRejectedError("The proposed query may use only saved-hotel tables.")
    limit_match = re.search(r"\blimit\s+([0-9]+)\s*$", lowered)
    if limit_match is None or int(limit_match.group(1)) > MAX_ROWS:
        raise ChatQueryRejectedError("The proposed query must use LIMIT 10 or less.")
    if normalized.count("?") != len(parameters) or len(parameters) > 12:
        raise ChatQueryRejectedError("The proposed query has invalid parameters.")
    if any(not isinstance(value, (str, int, float)) or isinstance(value, bool) for value in parameters):
        raise ChatQueryRejectedError("The proposed query has unsupported parameter values.")
    return normalized, tuple(parameters)


def execute_readonly_query(sql: str, parameters: tuple[Any, ...]) -> list[dict]:
    """Run a validated query through a SQLite read-only connection."""
    database_uri = f"{DATABASE_PATH.resolve().as_uri()}?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(sql, parameters).fetchall()
        if len(rows) > MAX_ROWS:
            raise ChatQueryRejectedError("The proposed query returned too many rows.")
        return [dict(row) for row in rows]
    except sqlite3.DatabaseError as error:
        raise ChatQueryRejectedError("The proposed query could not be run safely.") from error
    finally:
        connection.close()


def ask_hotel_assistant(question: str) -> dict:
    """Complete question → checked SQL → local retrieval → grounded answer."""
    cleaned_question = question.strip()
    if len(cleaned_question) < 3:
        raise ChatQueryRejectedError("Enter a more specific hotel question.")
    proposal_content = request_chat_completion(
        _proposal_prompt(cleaned_question), 500, expect_json=True
    )
    proposed_sql, proposed_parameters = _parse_sql_proposal(proposal_content)
    safe_sql, safe_parameters = validate_sql(proposed_sql, proposed_parameters)
    records = execute_readonly_query(safe_sql, safe_parameters)
    answer = request_chat_completion(_answer_prompt(cleaned_question, records), 450)
    return {
        "question": cleaned_question,
        "proposed_sql": safe_sql,
        "parameters": list(safe_parameters),
        "records": records,
        "answer": answer[:3000],
        "model": OPENROUTER_MODEL,
        "rates_and_availability_are_simulated": True,
    }
