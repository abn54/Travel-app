# Expedia Lite sample data

This directory contains the instructor-supplied fictional classroom data pack. It does not represent live hotel availability or real reservations.

## Files and relationships

- `hotels.csv`: one hotel per `hotel_id`.
- `trips.csv`: one offered stay per `trip_id`; `hotel_id` connects each stay to its hotel.
- `users.csv`: one demo traveler per `user_id`.
- `bookings.csv`: one simulated booking per `booking_id`; `user_id` and `trip_id` connect it to a traveler and stay.

The Part 1 CSV search reads only `hotels.csv` and `trips.csv`. The user and booking files remain unchanged for Part 2 SQLite seeding.

The CSV files use UTF-8 with a byte-order mark in the original data pack. The backend opens them with `utf-8-sig` so both the supplied files and ordinary UTF-8 CSV files read correctly.

## Part 1 check records

`Valley Trail Inn` returns stay `T008`. `Boston` returns `T001`, `T002`, `T009`, and `T010` when searched as a city. `Miami` has no matching stays.
