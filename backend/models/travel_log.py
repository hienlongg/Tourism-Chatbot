from __future__ import annotations
from typing import Dict, Any
from datetime import datetime
from flask import current_app
from tourism_chatbot.rag.rag_engine import slugify


def _get_db():
    """
    Get the MongoDB database instance for application data.
    Uses the shared client stored in Flask app config.
    """
    client = current_app.config["APP_MONGO_CLIENT"]
    db_name = current_app.config["APP_MONGO_DBNAME"]
    return client[db_name]


def upsert_location_cache(location: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert or update a location document in the 'locations' collection.
    Returns the stored document including the generated slug.
    """
    db = _get_db()

    name = str(location.get("name", "")).strip()
    if not name:
        raise ValueError("Location must have a name")

    slug = slugify(name)

    doc = {
        "slug": slug,
        "name": name,
        "address": location.get("address", ""),
        "lat": location.get("lat"),
        "lng": location.get("lng"),
        "description": location.get("description"),
        "imageUrl": location.get("imageUrl"),
        "source": location.get("source", "unknown"),
        "updatedAt": datetime.utcnow(),
    }

    db.locations.update_one(
        {"slug": slug},
        {
            "$set": doc,
            "$setOnInsert": {"createdAt": datetime.utcnow()},
        },
        upsert=True,
    )

    return doc


def add_visited_location(user_id: str, location_slug: str) -> int:
    """
    Add a visited location slug to the user's travel log.
    Returns the total number of visited locations after the update.
    """
    db = _get_db()

    db.user_travel_logs.update_one(
        {"userId": user_id},
        {
            "$setOnInsert": {"userId": user_id},
            "$addToSet": {
                "locations": {
                    "slug": location_slug,
                    "visitedAt": datetime.utcnow(),
                }
            },
        },
        upsert=True,
    )

    doc = db.user_travel_logs.find_one({"userId": user_id}, {"locations": 1, "_id": 0})
    locations = doc.get("locations", []) if doc else []
    return len(locations)


def get_user_travel_log(user_id: str) -> Dict[str, Any]:
    """
    Fetch the user's travel log and join each visited location with
    its detailed information from the locations cache.
    """
    db = _get_db()

    log = db.user_travel_logs.find_one({"userId": user_id}, {"_id": 0})
    if not log:
        return {"userId": user_id, "locations": []}

    slugs = [item["slug"] for item in log.get("locations", [])]

    locations_map = {
        loc["slug"]: loc
        for loc in db.locations.find({"slug": {"$in": slugs}}, {"_id": 0})
    }

    enriched_locations = []
    for item in log.get("locations", []):
        slug = item["slug"]
        visited_at = item.get("visitedAt")
        loc_detail = locations_map.get(slug)
        if not loc_detail:
            continue

        merged = dict(loc_detail)
        merged["visitedAt"] = visited_at
        enriched_locations.append(merged)

    return {
        "userId": user_id,
        "locations": enriched_locations,
    }
