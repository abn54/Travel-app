# Expedia Lite — Assignment 1 Part 2

## Repository and commit

Repository URL: https://github.com/abn54/Travel-app

Part 1 checkpoint preserved: `bb566a189aebf1d58b5c4ded2aadb622374c46ad`.

Assessed Part 2 commit: add the exact reviewed commit here after committing and pushing this Part 2 revision.

## Implementation

Since Part 1, Expedia Lite now stores all hotel, trip, traveler, and booking data in SQLite. A new database is seeded once from the four supplied CSV files, then every search and booking action reads or writes SQLite. The Vue View searches stays, lets a traveler create a simulated booking, displays history, cancels a booking while retaining its row, and deletes a test booking.

The backend was reorganized into MVC layers. `backend/models.py` defines request models, `backend/database.py` defines the relational SQLite schema and one-time seed, and `backend/travel_controller.py` owns the SQLite search and CRUD operations. `backend/api_routes.py` contains only thin FastAPI HTTP routes, while `backend/app.py` only configures application startup, CORS, and routing. The responsive Expedia-inspired Vue interface uses a navy header, yellow calls to action, clear cards, labeled tables, and visible confirmed/cancelled status pills to make the booking workflow easier to follow.

## Verification

| Action | Expected result | Observed result |
| --- | --- | --- |
| Search through the frontend | Searching `Valley Trail Inn` shows supplied available stay `T008` in a labeled table. | The local API returned `T008`, State College Trail Weekend, with the supplied dates and rates. |
| Seeded history after a browser refresh | The six supplied booking records remain available for the Part 2 workflow. | The refreshed Vue history table displayed `B001`–`B006`, including cancelled `B002` and `B006`. |
| Create through the frontend | Choose `T008` and Demo Traveler 6, then create a new booking. | A new confirmed booking appears in that traveler's history. |
| Read after browser refresh | Refresh the frontend and view booking history. | The created booking remains visible because it is stored in SQLite. |
| Update through the frontend | Cancel the created booking without removing the record. | Its status changes to `cancelled` and its history row remains. |
| Delete through the frontend | Create a separate test booking, then delete it. | The selected test booking is removed from history. |
| Restart persistence | Restart the frontend and backend, then read booking history. | Cancelled bookings remain and deleted test bookings remain absent; starter data is not duplicated. |
| Isolated controller verification, September 29, 2026 | Model, controller, routes, existing ZIP features, and persistence behavior remain correct after the MVC refactor. | 23 automated backend checks passed, including an isolated SQLite create → cancel → delete → restart test and the one-time legacy seed repair. The Vue production build passed. |

Screenshots: [booking form](screenshots/part2-booking-form.png) and [persisted booking history](screenshots/part2-booking-history.png).

## Demo video

Before submission, record a screen video under three minutes showing search, create, read after refresh, cancel, delete, and the frontend/backend restart persistence check. Add the accessible video link here. Do not show `.env` or API-key contents.

## Project context and next steps

- [README](../README.md)
- [Project instructions](../AGENTS.md)
- [Design note](design.md)
- [Selected prompts](../prompts/selected-prompts.md)
- [Current handoff](../handoffs/current.md)

Remaining limitation: this local classroom simulation has no authentication, payments, live inventory, or real reservations. Next: record the required Part 2 demo, commit and push the reviewed work, replace the commit placeholder above, then upload this `report.md` to Canvas.
