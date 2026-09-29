# Expedia Lite

Expedia Lite is a local Vue + FastAPI travel application for searching hotel stays, making simulated bookings, reviewing booking history, and discovering live nearby hotel locations.

## Run locally

1. In `backend/`, create and activate a virtual environment, then install `pip install -r requirements.txt`.
2. Start the API: `uvicorn app:app --reload --port 8000`.
3. In `frontend/`, run `npm install`, then `npm run dev`.
4. Open the local Vite URL (usually `http://localhost:5173`).

On the first backend startup, the app creates `backend/travel.db` from the four supplied CSV files. Later startups use the existing SQLite data without re-importing the starter rows.

## Assignment 1 Part 2 architecture

- `backend/models.py` holds booking request models.
- `backend/database.py` holds the SQLite schema, table relationships, connection setup, and one-time CSV seed.
- `backend/travel_controller.py` holds SQLite search and booking CRUD operations.
- `backend/api_routes.py` contains thin FastAPI routes that call the controllers and map errors to HTTP responses.
- `backend/app.py` only configures FastAPI, CORS, startup, and the route collection.

Vue remains the View: it collects user actions and renders search, booking, cancellation, deletion, and booking-history results returned by FastAPI.

## Configuration

The backend-only configuration helper at `backend/config.py` loads the project-root `.env` file beside `frontend/` and `backend/`. Edit `GEOAPIFY_API_KEY` there, never in frontend code. The key supports both Geoapify ZIP geocoding and hotel discovery. Restart the FastAPI backend after editing `.env` so it reloads the configuration.

Leaflet is installed in `frontend/` and displays OpenStreetMap tiles with attribution. It does not receive the Geoapify key.

## Assignment 2 Part 1 — Live hotel search and map

- `GET /api/hotel-discovery?postcode=<five-digit-zip>` validates the string, resolves that exact U.S. ZIP through Geoapify, then searches `accommodation.hotel` locations within 5 km of the returned center.
- The route distinguishes invalid input, unresolved ZIPs, missing configuration, provider failures, and a successful search with no nearby locations.
- Vue displays only provider-backed name, address, coordinates, and distance fields. A selected list item and map marker stay synchronized through the provider place ID.
- Results are location data, not an exhaustive inventory or proof of prices, ratings, availability, or bookings.

## Public API ZIP activity

- `GET /api/health` reports whether the backend key is configured without returning it.
- `GET /api/demo/zip-location` keeps the fixed `16802` classroom demonstration available.
- `GET /api/zip-location?postcode=16802` accepts an entered five-digit U.S. ZIP code and returns its safe location data or a clear error.
- The Vue ZIP form begins with `16802`, supports another five-digit ZIP, and displays the returned postcode, country code, locality, latitude, and longitude in a table.

## Features

- Search runs against SQLite hotel and trip records joined through `hotel_id`.
- Live hotel discovery runs through FastAPI and Geoapify; it is separate from the supplied hotel/stay model and does not add live results to SQLite.
- The frontend can create a booking for any supplied traveler and offered stay.
- Booking history reads from SQLite and lets the user cancel a booking while retaining it or delete a test booking.
- The supplied CSVs seed a new database once; existing bookings persist across refreshes and restarts.

## Part 2 checks

- Search `Valley Trail Inn`, select `T008`, and create a booking for Demo Traveler 6.
- Refresh the browser, cancel the new booking, and confirm that its cancelled row remains in history.
- Create a second test booking, delete it, then restart both services and confirm that the cancelled booking remains while the deleted booking does not return.

## Project context

- [Design note](docs/design.md)
- [Assignment 2 Part 1 research](docs/assignment2-part1-research.md)
- [Assignment 2 Part 1 early mockup](docs/mockups/assignment2-part1-early-mockup.svg)
- [Public API ZIP activity evidence](docs/public-api-evidence.md)
- [Current handoff](handoffs/current.md)
- [Selected prompts](prompts/selected-prompts.md)
- [Current Assignment 2 Part 1 report](report.md)
