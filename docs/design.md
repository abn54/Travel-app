# Expedia Lite design note

## Assignment 1 — SQLite bookings

The Vue frontend is the View. It presents one hotel-name-or-city search field, a labeled table of matching hotel stays, a traveler selector, and booking-history actions. It owns temporary interface state only. A selected stay and traveler are sent to FastAPI to create a simulated booking. The same interface requests booking history, sends a cancel request that retains the record, and sends a delete request for a test booking. Its navy, blue, and yellow header, cards, calls to action, status pills, and responsive tables use an Expedia-inspired visual hierarchy without copying Expedia content.

The backend follows Model–View–Controller responsibilities:

- `backend/models.py` defines the request models for new bookings and status updates. `backend/database.py` defines the SQLite travel model, including the hotel → trip and traveler/trip → booking relationships, connection setup, and the one-time CSV seed.
- `backend/travel_controller.py` is the database controller. It owns the SQLite search join, traveler lookup, booking-history join, unique booking-ID creation, status update, and deletion operations. It has no FastAPI route decorators.
- `backend/api_routes.py` is the thin HTTP controller layer. It validates HTTP payloads, calls the database controller, and maps known domain errors to safe responses. `backend/app.py` only initializes FastAPI, CORS, the database lifespan, and the route collection.

When `travel.db` does not exist, the database model creates SQLite tables for hotels, trips, users, bookings, and the next generated booking number; then it seeds the original four CSV files exactly once. The database controller returns display-ready stays and bookings. Create assigns a persistent unique `B###` ID, update changes `status` to `cancelled`, and delete removes only the selected booking.

SQLite is the Part 2 application data source. The CSV files remain as the initial seed source only. Each API request opens its own SQLite connection with foreign-key checks enabled, so browser refreshes and service restarts continue to show saved changes without duplicate starter records.

## ZIP lookup controller contract

`backend/location_controller.py` is a backend-only controller for entered five-digit U.S. ZIP codes. It reads the Geoapify key only through `backend/config.py`, sends it only in the backend's forward-geocoding request, and uses a five-second timeout. A matching U.S. postcode with valid latitude and longitude returns a small `resolved` location object containing `postcode`, `country_code`, `latitude`, `longitude`, and `locality` when available. A valid provider response without an acceptable matching location returns `unresolved`; missing configuration returns `configuration_error`; request, decoding, or malformed-provider failures return `provider_error`. Neither outcome exposes the key, provider URL, or raw exception text.

`GET /api/demo/zip-location` keeps the fixed `16802` classroom demonstration. `GET /api/zip-location?postcode=<zip>` passes an entered ZIP to the same controller. Both routes return a resolved location unchanged, map missing configuration to HTTP 503, map an unresolved ZIP to HTTP 404, and map provider failures to HTTP 502. Vue provides both the fixed demonstration button and a real ZIP input; its location result is displayed in a labeled table.

## Assignment 2 Part 1 — Live hotel discovery

`backend/hotel_discovery_controller.py` is separate from the supplied SQLite Hotel model because Geoapify places do not establish a nightly price or an offered stay. It validates the ZIP as five digits, reuses the backend-only ZIP controller to establish the exact U.S. postcode center, then calls Geoapify Places with `accommodation.hotel`, a 5 km circle filter, and a proximity bias. The controller normalizes only the provider place ID, optional name/address, coordinates, and optional distance. It reports invalid input, unresolved ZIP, configuration error, provider error, and successful empty results as distinct outcomes.

`GET /api/hotel-discovery` is a thin FastAPI route that maps those outcomes to safe HTTP responses. Vue submits the ZIP through that route, shows clear feedback for each state, and uses the provider place ID as the one selection key shared by the keyboard-accessible result cards and Leaflet markers. Leaflet uses attributed OpenStreetMap tiles; Geoapify credentials remain backend-only.

## Assignment 2 Part 2 — Local storage and RAG assistant

The finished Part 1 map remains a live provider-location tool. When a traveler chooses **Add to Local**, Vue sends only the displayed provider-backed location fields to FastAPI. `backend/local_hotel_controller.py` stores the provider `place_id`, location context, and one dated set of clearly labeled simulated course nightly rates and available-room counts. The `place_id` primary key prevents duplicate saves. Local lookup and removal also pass through FastAPI, so the saved hotel and its demo-night rows persist in SQLite after browser and backend restarts.

The chatbot follows a narrow RAG path. Vue sends its natural-language question only to `POST /api/hotel-chat`. `backend/hotel_chat_controller.py` sends the question, schema, and SQL rules to the backend-only OpenRouter client. It accepts exactly one bounded `SELECT` using `local_hotels` and `demo_hotel_nights`, rejects SQL comments, semicolons, writes, schema operations, unapproved tables, invalid parameters, and missing or excessive limits, then executes through SQLite's read-only URI connection. Only the original question and the resulting limited records are sent to the model for the second answer request. The controller returns the checked SQL, parameters, records, and answer to Vue, which presents all three without revealing a credential. Simulated data remains explicitly labeled, and the assistant cannot make bookings or change local data.
