# Expedia

Expedia is a local Vue + FastAPI Part 1 travel application for searching simulated hotel stays by hotel name or city.

## Run locally

1. In `backend/`, create and activate a virtual environment, then install `pip install -r requirements.txt`.
2. Start the API: `uvicorn app:app --reload --port 8000`.
3. In `frontend/`, run `npm install`, then `npm run dev`.
4. Open the local Vite URL (usually `http://localhost:5173`).

## Features

- The supplied `hotels.csv` and `trips.csv` are joined through `hotel_id`.
- FastAPI returns matching stays to a simple Vue table.
- A clear no-results message appears for unmatched hotel names or cities.
- The supplied `users.csv` and `bookings.csv` are retained unchanged for the later SQLite work.

## Part 1 checks

- Search `Valley Trail Inn`; one matching stay (`T008`) should appear.
- Search `Boston`; four matching stays should appear.
- Search `Miami`; the no-results message should appear.

## Project context

- [Design note](docs/design.md)
- [Current handoff](handoffs/current.md)
- [Selected prompts](prompts/selected-prompts.md)
- [Part 1 report template](report.md)
