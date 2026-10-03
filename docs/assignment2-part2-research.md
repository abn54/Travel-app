# Assignment 2 Part 2 — RAG assistant research notes

## Sources consulted

- [OpenRouter Free Models Router](https://openrouter.ai/openrouter/free) documents the free-router fallback and explains that availability can vary across free models.
- [NVIDIA Nemotron 3 Ultra on OpenRouter](https://openrouter.ai/nvidia/nemotron-3-ultra-550b-a55b-20260604%3Afree) documents the selected free Nemotron endpoint used for the chatbot's first attempt.
- [SQLite SELECT documentation](https://www.sqlite.org/lang_select.html) describes SQLite's read-query form and reinforces the decision to allow only narrow `SELECT` statements.
- [SQLite URI filenames](https://www.sqlite.org/uri.html) documents URI connection options, including the read-only connection mode used for the retrieval step.

## Patterns, risks, and decisions

A useful assistant makes its evidence inspectable instead of presenting an unsupported recommendation. The interface therefore keeps the original question, checked SQL, retrieved local rows, and final response together. It uses loading, result, no-match, and failure states rather than treating a model problem as an empty hotel result.

Natural-language-to-SQL is unsafe when the model can choose arbitrary schema operations. The assistant receives only the relevant local schema and returns a JSON SQL proposal. The backend permits one `SELECT`, only `local_hotels` and `demo_hotel_nights`, no comments or semicolon, parameter-count matching, and `LIMIT 10` or less. It then uses SQLite's read-only URI before sending the limited rows back to the model.

Live provider hotels remain location data only. The Local Hotels section is intentionally separate: when a traveler saves one provider location, SQLite creates a deterministic set of **simulated course** nightly rates and room counts for October 10–16, 2026. The UI labels those fields everywhere so they cannot be confused with Geoapify inventory or a booking promise.

OpenRouter requests remain in the Python backend. The selected free Nemotron endpoint is attempted first; the official OpenRouter free router is a resilience fallback when free-model capacity is unavailable. Neither model request is made by Vue, and the key never enters browser code.
