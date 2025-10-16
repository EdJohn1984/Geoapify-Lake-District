#!/usr/bin/env python3
"""
Build region waypoint files by filtering populated places that have both
at least one pub and at least one campsite within a nearby radius.

Usage:
  python scripts/analysis/build_region_waypoints.py "<west,south,east,north>" data/waypoints/<region>.json
"""
import os
import sys
import json
from typing import List, Tuple
from pathlib import Path

import requests
from geopy.distance import geodesic


API_KEY = os.getenv("GEOAPIFY_API_KEY", "01c9293b314a49979b45d9e0a5570a3f")
PLACES_CATEGORIES = "populated_place.town,populated_place.village,populated_place.city"
PUBS_CATEGORIES = "catering.pub"
CAMP_CATEGORIES = "camping.camp_site"
TIMEOUT_SECONDS = 30
NEARBY_KM = float(os.getenv("WAYPOINT_NEARBY_KM", "1.5"))


def fetch_places(bbox: str, categories: str, limit: int) -> List[dict]:
    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": categories,
        "filter": f"rect:{bbox}",
        "limit": limit,
        "apiKey": API_KEY,
    }
    response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()
    return data.get("features", [])


def to_latlon(feature: dict) -> Tuple[float, float]:
    lon, lat = feature["geometry"]["coordinates"]
    return (lat, lon)


def dedupe_by_coords(features: List[dict]) -> List[dict]:
    seen = set()
    unique = []
    for f in features:
        lat, lon = to_latlon(f)
        key = (round(lat, 6), round(lon, 6))
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


def normalize_place(feature: dict) -> dict:
    props = feature.get("properties", {})
    name = props.get("name") or props.get("address_line1") or "Unnamed"
    props["name"] = name
    feature["properties"] = props
    return feature


def build_waypoints_for_bbox(bbox: str) -> List[dict]:
    places = fetch_places(bbox, PLACES_CATEGORIES, limit=500)
    pubs = fetch_places(bbox, PUBS_CATEGORIES, limit=500)
    camps = fetch_places(bbox, CAMP_CATEGORIES, limit=500)

    pub_pts = [to_latlon(p) for p in pubs]
    camp_pts = [to_latlon(c) for c in camps]

    kept: List[dict] = []
    for place in places:
        plat, plon = to_latlon(place)
        has_pub = any(geodesic((plat, plon), pub).km <= NEARBY_KM for pub in pub_pts)
        if not has_pub:
            continue
        has_camp = any(geodesic((plat, plon), camp).km <= NEARBY_KM for camp in camp_pts)
        if not has_camp:
            continue
        kept.append(normalize_place(place))

    return dedupe_by_coords(kept)


def main():
    if len(sys.argv) != 3:
        print("Usage: build_region_waypoints.py <bbox_w,s,e,n> <out_file>")
        sys.exit(1)

    bbox = sys.argv[1]
    out_path = Path(sys.argv[2])

    waypoints = build_waypoints_for_bbox(bbox)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(waypoints, f, indent=2)

    print(f"Saved {len(waypoints)} waypoints to {out_path}")


if __name__ == "__main__":
    main()


