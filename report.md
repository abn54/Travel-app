# Expedia Lite — Assignment 2 Part 1

## Project access

Repository URL: https://github.com/abn54/Travel-app

Assessed Part 1 commit: [`b3ffc44071cc0cfe5548c8c8d2b41b83c82fd989`](https://github.com/abn54/Travel-app/commit/b3ffc44071cc0cfe5548c8c8d2b41b83c82fd989)

To run locally, install `backend/requirements.txt`, run `uvicorn app:app --reload --port 8000` from `backend/`, then run `npm install` and `npm run dev` from `frontend/`. Set `GEOAPIFY_API_KEY` only in the project-root `.env`; restart the backend after editing it. Leaflet is installed through the frontend dependencies and uses attributed OpenStreetMap tiles without receiving the Geoapify key.

## Research notes

[Research notes](docs/assignment2-part1-research.md) record the Geoapify, Leaflet, and hotel-map sources consulted, useful interaction patterns, limitations, and the resulting decisions. The application uses the returned U.S. ZIP location as the search center, requests `accommodation.hotel` locations only within a 5 km circle, and does not invent price, rating, availability, or booking data.

## Early mockup

![Early Part 1 mockup](docs/mockups/assignment2-part1-early-mockup.svg)

The mockup was prepared before implementation. The final interface retains the ZIP search, distinct state feedback, synchronized list/map selection, 5 km center label, and map attribution. Styling and responsive layout were refined during implementation.

## Screen-recorded demo

Record and link a short browser demonstration before submission. Show ZIP `16802`, the returned nearby-hotel list and map, a list selection followed by a marker selection, and one clear error state. Do not show `.env` or the API key.

Current browser evidence: [live hotel map screenshot](docs/screenshots/assignment2-part1-live-map.png).

## Verification record

| Date and action | Expected result | Observed result |
| --- | --- | --- |
| September 26, 2026 — direct `GET /api/hotel-discovery?postcode=16802` | Resolve the requested U.S. ZIP before Places search, then return only locations within 5 km. | The request resolved `16802` to State College and returned 20 provider hotel locations with provider place IDs, names/addresses, coordinates, and distances. |
| September 26, 2026 — search `16802` in Vue | Show a result list and an attributed map centered on the returned ZIP, without prices or booking claims. | Vue displayed 20 nearby hotel locations and the map center label `16802 · State College`. |
| September 26, 2026 — click a result card, then a map marker | The matching representation becomes selected in both directions. | Browser verification confirmed list-to-marker and marker-to-list synchronization; the selected location was Nittany Lion Inn. |
| Mocked invalid, unresolved, no-result, and provider-failure paths | Input and request states are distinct; a failure is not presented as an empty result. | 20 backend checks passed. Invalid input maps to a clear 422 response, unresolved ZIP maps to 404, provider failure maps to 502, and an empty provider feature list remains a successful `no_results` response. |
| September 29, 2026 — restore and test the local services | The ZIP tool and live nearby-hotel search work when both local services are running. | The backend health check safely reported that the key is configured. Direct ZIP `16802` returned State College coordinates, the browser ZIP table displayed the same fields, and the nearby-hotel search displayed provider results and an attributed map. |
| September 29, 2026 — live nearby search, list click, then map-marker click | ZIP `16802` returns provider hotel locations around the resolved center; list and marker selection stay synchronized. | The browser returned 20 nearby provider hotel locations around `16802 · State College`. Selecting Nittany Lion Inn from the list changed its map marker, and selecting a different map marker changed the matching list card. |

Live coverage changes over time, so the recorded observation is not used as a fixed expected result count.

## AI disclosure and evidence log

- Codex, based on GPT-5, was used to inspect the project, research official Geoapify and Leaflet documentation, implement the FastAPI controller/route and Vue map/list view, write mocked checks, and run local verification.
- The selected prompts and a revised browser-testing approach are recorded in [selected prompts](prompts/selected-prompts.md). The first browser automation attempt did not populate the ZIP field; it was revised to dispatch normal input and form-submit events before the successful synchronization check.
- Geoapify supplied live location data. Leaflet rendered the map with OpenStreetMap attribution. Neither service received or exposed the project’s `.env` value in the report, screenshots, or browser code.

## Project context and next steps

- [README](README.md)
- [Project instructions](AGENTS.md)
- [Design note](docs/design.md)
- [Research notes](docs/assignment2-part1-research.md)
- [Selected prompts](prompts/selected-prompts.md)
- [Current handoff](handoffs/current.md)

Remaining limitation: live provider coverage and fields vary, and Part 1 intentionally has no persistent shortlist. Next: record the linked browser demo and upload this `report.md`.
