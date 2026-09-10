# Expedia Part 1 design note

The Vue frontend presents one hotel-name-or-city search field, a Search button, and a plain table of matching hotel stays. It owns temporary interface state and sends the search request to FastAPI.

FastAPI reads the instructor-supplied `hotels.csv` and `trips.csv`, connects a trip to its hotel through `hotel_id`, filters the joined records by hotel name or city, calculates the number of nights and estimated stay price, and returns the matching records to Vue. A no-result response is an empty list, which Vue presents as a clear message.

CSV files are the Part 1 data source. `users.csv` and `bookings.csv` are retained unchanged for Part 2. SQLite and CRUD are intentionally deferred to Part 2.
