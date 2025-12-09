from __future__ import annotations
from flask import Blueprint, request, jsonify, session
from backend.middlewares.decorators import login_required
from backend.utils.location_extractor import resolve_location_by_name
from backend.utils.image_resolver import enrich_location_with_image
from backend.models.travel_log import (
    upsert_location_cache,
    add_visited_location,
    get_user_travel_log,
    remove_visited_location,
    update_visited_location_note,
)
import logging

logger = logging.getLogger(__name__)

travel_log_bp = Blueprint("travel_log", __name__, url_prefix="/api/travel-log")


def _get_current_user_id() -> str:
    """
    Helper to retrieve the current logged-in user's id from the session.
    """
    return session.get("user_id", "anonymous")


@travel_log_bp.route("/visited", methods=["POST"])
@login_required
def add_visited():
    """
    User submits a place name or address they have visited.

    Flow:
      1. Resolve name/address via CSV + OSM.
      2. Ensure imageUrl is present (CSV or Google CSE).
      3. Cache location in MongoDB.
      4. Add slug to user's travel log.
    """
    data = request.get_json() or {}
    raw_name = str(data.get("name", "")).strip()

    if not raw_name:
        return jsonify({"success": False, "error": "Location name is required."}), 400

    user_id = _get_current_user_id()
    logger.info(f"[travel_log] User {user_id} submitted visited place: {raw_name}")

    # 1) Resolve location (CSV + OSM)
    location = resolve_location_by_name(raw_name)
    if not location:
        return jsonify({
            "success": False,
            "error": "The location you entered is invalid or could not be found."
        }), 404

    # 2) Ensure we have an imageUrl
    location = enrich_location_with_image(location)

    # 3) Cache normalized location
    cached_doc = upsert_location_cache(location)
    slug = cached_doc["slug"]

    # 4) Add to user's travel log
    visited_count = add_visited_location(user_id, slug)

    return jsonify({
        "success": True,
        "location": cached_doc,
        "visitedCount": visited_count,
    }), 200



@travel_log_bp.route("/visited/<slug>", methods=["DELETE"])
@login_required
def remove_visited(slug):
    """
    Remove a place from the user's travel log.
    """
    user_id = _get_current_user_id()
    new_count = remove_visited_location(user_id, slug)
    return jsonify({"success": True, "visitedCount": new_count}), 200


@travel_log_bp.route("/visited/<slug>", methods=["PUT"])
@login_required
def update_note(slug):
    """
    Update the personal note for a visited location.
    JSON Body: { "note": "..." }
    """
    user_id = _get_current_user_id()
    data = request.get_json() or {}
    note = data.get("note", "").strip()

    # Note: We allow empty notes (clearing the note)
    
    success = update_visited_location_note(user_id, slug, note)
    
    if not success:
         # If slug doesn't exist in user log, we could return 404, 
         # but update_one returns modified_count=0 if nothing matched.
         # It's possible the user just hasn't visited it yet or slug is wrong.
         # For UI consistency we might just return success=False.
         # But usually if they are editing, it exists.
         return jsonify({"success": False, "error": "Location not found in travel log"}), 404

    return jsonify({"success": True}), 200



@travel_log_bp.route("", methods=["GET"])
@login_required
def get_log():
    """
    Return the current user's travel log with detailed location data.
    """
    user_id = _get_current_user_id()
    log = get_user_travel_log(user_id)

    return jsonify({
        "success": True,
        "userId": user_id,
        "visitedCount": len(log["locations"]),
        "locations": log["locations"],
    }), 200