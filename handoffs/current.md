# Current handoff

## What works

Part 2 uses `travel.db` for search, traveler lookup, simulated booking, booking history, cancellation, and deletion. The original CSV records seed a new database once. The Vue frontend sends every data action through FastAPI and has simple forms and labeled tables for the full workflow. The Assignment 1 backend now separates request models (`backend/models.py`), the relational SQLite model and seed (`backend/database.py`), the SQLite CRUD controller (`backend/travel_controller.py`), thin FastAPI routes (`backend/api_routes.py`), and application setup (`backend/app.py`).

The public API ZIP activity adds a backend-only Geoapify lookup. The root `.env` remains outside version control; `backend/config.py` loads it through an explicit project-root path, and `/api/health` reports only whether the key is configured. The Vue app retains the fixed **Look up ZIP 16802** demonstration and adds a real five-digit ZIP input with a returned-location table.

Assignment 2 Part 1 adds `GET /api/hotel-discovery`. It resolves the exact requested U.S. ZIP first and searches Geoapify `accommodation.hotel` locations within a 5 km circle around that returned center. Vue presents provider-backed hotel cards and a Leaflet map, synchronized through the provider place ID. No shortlist behavior has been added.

## Checked

SQLite support was confirmed in the project virtual environment, so no SQLite installation was needed. Source validation confirmed 8 hotels, 12 trips, 6 users, 6 bookings, and valid relationships. After the MVC refactor, 23 automated backend checks passed, including an isolated SQLite create → cancel → delete → restart sequence. The production Vue build passed. A controlled local backend restart preserved all six supplied booking rows; the refreshed browser displayed cancelled `B006` and no duplicated seeds. A one-time legacy migration repairs only an older unmarked database with an empty booking table; it records a seed marker so future user deletions are never reloaded. Screenshots are in `docs/screenshots/` and details are in `report.md`.

For the public API activity, mocked controller and route checks covered valid input, invalid input, unresolved locations, missing configuration, and provider failure. A direct local `16802` request resolved State College with usable coordinates. The health endpoint reported `key is configured` without returning a key. Browser checks confirmed both the fixed button calls `/api/demo/zip-location` and the editable ZIP input displays `16802` in the labeled results table. The key-free screenshot is in `docs/screenshots/public-api-zip-table.png`; details are in `docs/public-api-evidence.md`.

For Assignment 2 Part 1, 20 mocked backend checks passed, the Vite production build passed, and a live search on September 26, 2026 for `16802` resolved State College and returned 20 provider hotel locations. Browser verification selected a result card and then a map marker; each selected the matching representation. Evidence is in `docs/screenshots/assignment2-part1-live-map.png` and the research/mocking artifacts are in `docs/assignment2-part1-research.md` and `docs/mockups/assignment2-part1-early-mockup.svg`.

On September 29, 2026, the local backend environment was restored from `backend/requirements.txt`. The local health endpoint safely confirmed the configured-key status, direct ZIP `16802` returned State College coordinates, the Vue ZIP table displayed the same response, and the nearby-hotel search displayed provider results and its attributed map.

## Limitation and next task

This is a local classroom simulation. Authentication, payments, live inventory, and cancellation policies are outside the assignment data model. The current root `report.md` is for Assignment 2 Part 1; the preserved Assignment 1 Part 2 report is `docs/assignment1-part2-report.md`. Next, record the Assignment 2 Part 1 browser demonstration (enter `16802`, show the returned list and map, demonstrate list/map selection synchronization, and show one error state), add its accessible link and assessed commit to `report.md`, then submit it. Do not include `.env` or an API key.
