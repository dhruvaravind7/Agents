import math
import re
import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


async def search_nearby(lat, lng, amenity, radius=800):
    if not lat or not lng or not amenity:
        raise ValueError("lat, lng, amenity required")

    safe_amenity = re.sub(r'["\\]', "", str(amenity))

    query = f"""
[out:json][timeout:25];
(
  node["amenity"="{safe_amenity}"](around:{math.floor(radius)},{lat},{lng});
  way["amenity"="{safe_amenity}"](around:{math.floor(radius)},{lat},{lng});
  relation["amenity"="{safe_amenity}"](around:{math.floor(radius)},{lat},{lng});
);
out center;
"""

    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.post(
            OVERPASS_URL, content=query, headers={"Content-Type": "text/plain"}
        )
        res.raise_for_status()
        data = res.json()

    elements = data.get("elements", [])
    if not isinstance(elements, list):
        elements = []

    results = []
    for e in elements:
        t = e.get("tags") or {}
        out_lat = e.get("lat") or (e.get("center") or {}).get("lat")
        out_lng = e.get("lon") or (e.get("center") or {}).get("lon")

        place = {
            "name": t.get("name") or t.get("name:en") or "Unknown",
            "lat": f"{float(out_lat):.5f}" if out_lat is not None else None,
            "lng": f"{float(out_lng):.5f}" if out_lng is not None else None,
        }

        if t.get("opening_hours"):
            place["hours"] = t["opening_hours"]
        if t.get("cuisine"):
            place["cuisine"] = t["cuisine"]
        phone = t.get("phone") or t.get("contact:phone")
        if phone:
            place["phone"] = phone
        website = t.get("website") or t.get("contact:website")
        if website:
            place["website"] = website
        parts = [t.get("addr:housenumber"), t.get("addr:street")]
        address = " ".join(p for p in parts if p)
        if address:
            place["address"] = address

        results.append(place)

    return results
