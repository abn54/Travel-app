# Expedia startup prompts

## 1. Project boundary

Work only in this Expedia project. Keep Vue code in `frontend/` and FastAPI code in `backend/`. Keep the frontend dependent on FastAPI rather than reading CSV or SQLite files directly. Update README, design note, handoff, and report evidence when behavior changes.

## 2. Python and backend preparation

Check the project virtual environment first. Confirm that FastAPI, Uvicorn, and Python's built-in SQLite module are available. Do not install SQLite when the module is already present. Keep the Part 1 CSV search working while preparing Part 2.

## 3. Node and Vue preparation

Check `frontend/package.json`, install the existing dependencies if needed, and run the production build. Keep the interface limited to the assigned workflow.

## 4. Data and persistence preparation

Inspect the supplied `hotels.csv`, `trips.csv`, `users.csv`, and `bookings.csv` files before writing a SQLite schema. Preserve their existing IDs and relationships. Seed SQLite only when the database is new; never duplicate starter records on a later restart. Stop and report a missing source file rather than inventing records.

## 5. Verification loop

Use one small change at a time, then run the relevant check and correct confirmed failures before continuing. The Part 1 smoke test is: search `Valley Trail Inn`; expect one matching stay (`T008`). Then search `Miami`; expect the clear no-results message. Also search `Boston`; expect four matching stays. For Part 2, add a booking through the frontend, verify it in history, cancel it while retaining it, delete a test booking, then verify persistence after restart. Do not change unrelated files or add dependencies without first checking whether they are needed.
