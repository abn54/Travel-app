# Expedia

Expedia is a local Vue + FastAPI travel application for searching hotel stays, making simulated bookings, and reviewing booking history.

## Run locally

1. In `backend/`, create and activate a virtual environment, then install `pip install -r requirements.txt`.
2. Start the API: `uvicorn app:app --reload --port 8000`.
3. In `frontend/`, run `npm install`, then `npm run dev`.
4. Open the local Vite URL (usually `http://localhost:5173`).

On the first backend startup, the app creates `backend/travel.db` from the four supplied CSV files. Later startups use the existing SQLite data without re-importing the starter rows.

## Features

- Search runs against SQLite hotel and trip records joined through `hotel_id`.
- The frontend can create a booking for any supplied traveler and offered stay.
- Booking history reads from SQLite and lets the user cancel a booking while retaining it or delete a test booking.
- The supplied CSVs seed a new database once; existing bookings persist across refreshes and restarts.

## Part 2 checks

- Search `Valley Trail Inn`, select `T008`, and create a booking for Demo Traveler 6.
- Refresh the browser, cancel the new booking, and confirm that its cancelled row remains in history.
- Create a second test booking, delete it, then restart both services and confirm that the cancelled booking remains while the deleted booking does not return.

## Project context

- [Design note](docs/design.md)
- [Current handoff](handoffs/current.md)
- [Selected prompts](prompts/selected-prompts.md)
- [Part 2 report](report.md)
