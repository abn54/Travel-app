# RAG Context — Expedia Lite

## Prompt and retrieved schema

The backend loads [hotel-assistant.md](../prompts/hotel-assistant.md) during
FastAPI startup. The first model request receives that versioned context plus
relevant saved user/assistant conversation history. It proposes a single
bounded SQLite `SELECT`; FastAPI validates it, retrieves rows using a
read-only connection, then sends the original question and those rows to
OpenAI for the final grounded answer.

The saved-hotel JOIN path is:

```text
saved_hotels.hotel_id
  → saved_hotel_zips.hotel_id
  → demo_hotel_nights.hotel_id
```

`nightly_rate_usd` and `available_rooms` are simulated classroom data. A
missing date row is unknown availability, not availability.

## Planned live verification

Question:

```text
Show the three cheapest saved hotels near ZIP 16803 with at least one room
available for the night of October 11, 2026.
```

Expected proposal shape:

```sql
SELECT h.name, z.postcode, n.stay_date, n.nightly_rate_usd, n.available_rooms
FROM saved_hotels h
JOIN saved_hotel_zips z ON z.hotel_id = h.hotel_id
JOIN demo_hotel_nights n ON n.hotel_id = h.hotel_id
WHERE z.postcode = ? AND n.stay_date = ? AND n.available_rooms > 0
ORDER BY n.nightly_rate_usd ASC
LIMIT 3
```

Expected parameters are `16803` and `2026-10-11`. The result, answer, and
conversation ID must be recorded here after a live successful request.

## Current verification status — October 6, 2026

- The prompt loads at backend startup; OpenAI configuration and model
  availability were confirmed without exposing a key.
- Mocked backend checks verify user → proposed SQL → executed SQL → retrieval
  result → assistant answer, a no-match answer, follow-up history, blocked
  writes, and persisted traces after reopening SQLite.
- The account returned a rate-limit response to a minimal live completion.
  The backend saved a `provider_error` stage and returned a safe browser error;
  it did not fabricate an assistant answer.

When API capacity is available, run the planned question, copy the returned
SQL, rows, answer, and conversation ID here, then repeat with a no-match date
and inspect `conversation_messages` in DB Explorer after a backend restart.
