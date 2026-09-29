# Expedia Lite startup prompts

## 1. Project boundary

Work only in this Expedia Lite project. Keep Vue code in `frontend/` and FastAPI code in `backend/`. Keep the frontend dependent on FastAPI rather than reading CSV or SQLite files directly. Update README, design note, handoff, and report evidence when behavior changes.

## 2. Python and backend preparation

Check the project virtual environment first. Confirm that FastAPI, Uvicorn, and Python's built-in SQLite module are available. Do not install SQLite when the module is already present. Confirm that Part 2 search and booking actions use SQLite rather than reading CSV files per request.

## 3. Node and Vue preparation

Check `frontend/package.json`, install the existing dependencies if needed, and run the production build. Keep the interface limited to the assigned workflow.

## 4. Data and persistence preparation

Inspect the supplied `hotels.csv`, `trips.csv`, `users.csv`, and `bookings.csv` files before writing a SQLite schema. Preserve their existing IDs and relationships. Seed SQLite only when the database is new; never duplicate starter records on a later restart. Generate a new booking ID from a persistent sequence so deleting a booking does not reuse its ID. Stop and report a missing source file rather than inventing records.

## 5. Verification loop

Use one small change at a time, then run the relevant check and correct confirmed failures before continuing. The Part 2 smoke test is: search `Valley Trail Inn`; expect stay `T008`. Create a booking for Demo Traveler 6 through the frontend, refresh and verify it in history, cancel it while retaining its row, create and delete a second test booking, then restart the frontend and backend. The cancelled booking must remain, the deleted booking must remain absent, and starter data must not duplicate. Do not change unrelated files or add dependencies without first checking whether they are needed.

For Assignment 2 Part 1, inspect the Geoapify and Leaflet documentation and the early mockup first. Check whether Leaflet is installed before changing dependencies; obtain approval before installing it. Mock a valid provider location, an invalid ZIP, an unresolved ZIP, a successful empty response, and a provider failure. Then use one live U.S. ZIP, verify the returned center and map/list result data, and confirm that selecting either a result card or a marker selects the corresponding item in the other representation. Do not add shortlist persistence until Part 2 is requested.
