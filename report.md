# Expedia — Part 1

## Repository and commit

Repository URL: [https://github.com/abn54/Travel-app](https://github.com/abn54/Travel-app).

Exact submitted commit: `bb566a189aebf1d58b5c4ded2aadb622374c46ad`.

## Implementation

Expedia uses a Vue frontend for one hotel-name-or-city search input, a Search button, and a plain table of matching offered stays. FastAPI reads the instructor-supplied `hotels.csv` and `trips.csv`, connects each trip to its hotel through `hotel_id`, matches hotel names or cities without regard to capitalization, calculates nights and estimated stay price, and returns the joined records to Vue. The supplied `users.csv` and `bookings.csv` remain unchanged for Part 2.

## Verification

| Action | Expected result | Observed result |
| --- | --- | --- |
| Search Valley Trail Inn | One matching offered stay, `T008`, appears in the labeled table. | The browser showed the `T008` Valley Trail Inn row with its dates, nights, nightly rate, and estimated stay price. FastAPI returned the same joined record. |
| Search Boston | Four matching offered stays, `T001`, `T002`, `T009`, and `T010`, appear in the labeled table. | The browser showed four data rows; FastAPI returned the same four trip IDs. |
| Search Miami | A clear no-results message appears. | The browser showed “No hotel stays match ‘Miami’. Try another hotel name or city.” FastAPI returned an empty list. |

Screenshots: [successful search](docs/screenshots/successful-search.png) and [no-results search](docs/screenshots/no-results-search.png).

## Project context and next steps

- [README](README.md)
- [Project instructions](AGENTS.md)
- [Design note](docs/design.md)
- [Selected prompts](prompts/selected-prompts.md)
- [Current handoff](handoffs/current.md)

Part 1 is complete with the supplied CSV data. SQLite, simulated booking, booking history, and CRUD are intentionally deferred to Part 2.
