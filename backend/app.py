"""Expedia FastAPI service: CSV hotel-stay search for Part 1."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

DATA_DIR = Path(__file__).resolve().parent / "data"

app = FastAPI(title="Expedia Part 1 API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/search")
def search(hotel_name: str = "") -> list[dict]:
    """Join CSV hotel stays and match a hotel name or supplied-data city."""
    query = hotel_name.strip().casefold()
    if not query:
        return []

    with (DATA_DIR / "hotels.csv").open(newline="", encoding="utf-8-sig") as hotels_file, (DATA_DIR / "trips.csv").open(newline="", encoding="utf-8-sig") as trips_file:
        hotels = {row["hotel_id"]: row for row in csv.DictReader(hotels_file)}
        matches = []
        for trip in csv.DictReader(trips_file):
            hotel = hotels.get(trip["hotel_id"])
            if hotel is None:
                continue
            if query in hotel["hotel_name"].casefold() or query in hotel["city"].casefold():
                check_in = date.fromisoformat(trip["check_in"])
                check_out = date.fromisoformat(trip["check_out"])
                nights = (check_out - check_in).days
                nightly_rate = float(hotel["nightly_rate_usd"])
                matches.append(
                    {
                        "trip_id": trip["trip_id"],
                        "hotel_id": hotel["hotel_id"],
                        "hotel_name": hotel["hotel_name"],
                        "city": hotel["city"],
                        "state": hotel["state"],
                        "trip_name": trip["trip_name"],
                        "nightly_rate": nightly_rate,
                        "check_in": trip["check_in"],
                        "check_out": trip["check_out"],
                        "nights": nights,
                        "stay_price": nights * nightly_rate,
                    }
                )
    return matches
