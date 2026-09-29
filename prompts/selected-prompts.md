# Selected prompts

- “Build” followed by the Assignment 1 Travel Application brief.
- Follow-up scope correction: “wanted you to just to do first part for now”.
- Finalization: replace the temporary data with the instructor-supplied CSV pack, retain all four CSV files in `backend/data/`, and verify the Part 1 search against known records.
- Part 2: seed SQLite once from all four supplied CSV files; implement search, simulated booking, history, cancellation, deletion, and persistence checks through the Vue frontend and FastAPI.
- Assignment 1 Part 2 revision: separate the request models, SQLite schema/seed, database CRUD controller, thin FastAPI routes, and application startup after review identified that schema, routes, and CRUD logic had been combined in `app.py`. Keep all existing endpoints working and verify create, cancel, delete, and restart persistence in an isolated SQLite test.
- Assignment 2 Part 1: research Geoapify Places and Leaflet; create an early ZIP/list/map mockup; resolve the exact U.S. ZIP through FastAPI, fetch provider hotel locations within 5 km, and synchronize keyboard-accessible list selections with Leaflet markers. Keep keys backend-only and do not add shortlist behavior.
- Revision during browser verification: the first automated interaction did not populate the ZIP input. The check was revised to dispatch the browser’s normal input and form-submit events, then confirmed list-to-marker and marker-to-list synchronization.
