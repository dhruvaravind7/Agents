import asyncio
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse

from cache import cache
from places import search_nearby
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

COLS = ["name", "lat", "lng", "hours", "cuisine", "phone", "website", "address"]


def format_table(rows: list[dict]) -> str:
    if not rows:
        return "(no results)\n"

    headers = [c for c in COLS if any(r.get(c) is not None for r in rows)]
    widths = [max(len(h), max(len(str(r.get(h) or "")) for r in rows)) for h in headers]

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    def row(cells):
        return "|" + "|".join(f" {str(c or '').ljust(w)} " for c, w in zip(cells, widths)) + "|"

    lines = [sep, row(headers), sep]
    for r in rows:
        lines.append(row([r.get(h) for h in headers]))
    lines.append(sep)
    return "\n".join(lines) + "\n"


@app.get("/", response_class=PlainTextResponse)
async def root():
    return "Server is running\n"

@app.get("/nearby", response_class=PlainTextResponse)
async def nearby(
    lat: float = Query(...),
    lng: float = Query(...),
    type: str = Query(...),
    radius: float = Query(default=800),
):
    logger.info("Received request: lat=%s lng=%s type=%s radius=%s", lat, lng, type, radius)

    cache_key = f"nearby:{lat}:{lng}:{radius}:{type}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        results = await asyncio.wait_for(
            search_nearby(lat=lat, lng=lng, amenity=type, radius=radius),
            timeout=15,
        )
    except asyncio.TimeoutError:
        return PlainTextResponse('{"error":"overpass_timeout"}', status_code=504, media_type="application/json")

    table = format_table(results)
    cache.set(cache_key, table)
    return table


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3000"))
    logger.info("Server listening on %s", port)
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
