# Expedia — Part 2

## Repository and commit

Repository URL: [https://github.com/abn54/Travel-app](https://github.com/abn54/Travel-app).

Part 1 checkpoint preserved: `bb566a189aebf1d58b5c4ded2aadb622374c46ad`.

Exact submitted Part 2 commit: pending final merge to `main`.

## Implementation

Since Part 1, Expedia now creates `travel.db` from all four supplied CSV files only when no database exists. FastAPI owns the SQLite schema, initial seed, search joins, traveler lookup, and booking CRUD. The Vue frontend searches stays, lets a user choose a traveler and create a booking, reads booking history, cancels a booking without deleting it, and deletes a test booking. After seeding, all application reads and writes use SQLite.

## Verification

| Action | Expected result | Observed result |
| --- | --- | --- |
| Create through the frontend | Choose `T008` and Demo Traveler 6, then create a new booking. | The browser created `B008` and showed it as confirmed in Demo Traveler 6’s history. |
| Read after browser refresh | Refresh the frontend and view booking history. | `B008` remained visible in history after the refresh. |
| Update through the frontend | Cancel `B008` without removing the record. | The browser changed `B008` to `cancelled` and retained its history row. |
| Delete through the frontend | Create test booking `B009`, then delete it. | The browser removed `B009`; it was absent from history after deletion. |
| Restart persistence | Restart the frontend and backend, then read the database and browser history. | `B008` remained cancelled, `B009` remained absent, and SQLite had seven bookings: the six seeds plus `B008`, with no duplicate seed rows. |

Screenshots: [booking form](docs/screenshots/part2-booking-form.png) and [persisted booking history](docs/screenshots/part2-booking-history.png).

## Project context and next steps

- [README](README.md)
- [Project instructions](AGENTS.md)
- [Design note](docs/design.md)
- [Selected prompts](prompts/selected-prompts.md)
- [Current handoff](handoffs/current.md)

Remaining limitation: this local classroom simulation has no authentication, payments, live inventory, or real reservations. Next: merge the reviewed Part 2 feature branch to `main`, push it, and upload this updated `report.md` to the Part 2 submission.
