# Expedia Part 2 design note

The Vue frontend presents one hotel-name-or-city search field, a plain table of matching hotel stays, and a Book button for each stay. It owns temporary interface state only. A selected stay and traveler are sent to FastAPI to create a simulated booking. The same interface requests booking history, sends a cancel request that retains the record, and sends a delete request for a test booking.

FastAPI owns database initialization and CRUD. When `travel.db` does not exist, it creates SQLite tables for hotels, trips, users, bookings, and the next generated booking number; then it seeds the original four CSV files exactly once. The FastAPI search and history routes join SQLite rows to return display-ready stays and bookings. Create assigns a persistent unique `B###` ID, update changes `status` to `cancelled`, and delete removes only the selected booking.

SQLite is the Part 2 application data source. The CSV files remain as the initial seed source only. Each API request opens its own SQLite connection with foreign-key checks enabled, so browser refreshes and service restarts continue to show saved changes without duplicate starter records.
