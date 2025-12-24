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


@travel_log_bp.route("/save", methods=["POST"])
@login_required
def save_location():
    """
    Save or unsave a location (bookmark).
    
    Request Body:
        name: str - Location name
        address: str - Location address (optional)
        lat: float - Latitude (optional)
        lng: float - Longitude (optional)
        description: str - Description (optional)
        imageUrl: str - Image URL (optional)
        
    Returns:
        200: Save toggled successfully
    """
    try:
        from flask import current_app
        
        data = request.get_json() or {}
        location_name = str(data.get("name", "")).strip()
        
        if not location_name:
            return jsonify({"success": False, "error": "Location name is required"}), 400
        
        user_id = _get_current_user_id()
        
        # Get MongoDB database
        db = current_app.config["APP_MONGO_CLIENT"][current_app.config["APP_MONGO_DBNAME"]]
        
        # Check if location is already saved
        saved_location = db.saved_locations.find_one({
            "userId": user_id,
            "name": location_name
        })
        
        if saved_location:
            # Unsave - remove from saved_locations
            db.saved_locations.delete_one({
                "userId": user_id,
                "name": location_name
            })
            is_saved = False
            message = "Location removed from saved"
        else:
            # Save - add to saved_locations
            from datetime import datetime, timezone as tz
            
            location_data = {
                "userId": user_id,
                "name": location_name,
                "address": data.get("address", ""),
                "lat": data.get("lat"),
                "lng": data.get("lng"),
                "description": data.get("description", ""),
                "imageUrl": data.get("imageUrl", ""),
                "savedAt": datetime.now(tz.utc)
            }
            
            db.saved_locations.insert_one(location_data)
            is_saved = True
            message = "Location saved successfully"
        
        logger.info(f"Location '{location_name}' {'saved' if is_saved else 'unsaved'} by user {user_id}")
        
        return jsonify({
            "success": True,
            "message": message,
            "isSaved": is_saved
        }), 200
        
    except Exception as e:
        logger.error(f"Error toggling save location: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@travel_log_bp.route("/saved-status", methods=["POST"])
@login_required
def check_location_saved_status():
    """
    Check if a location is saved by current user.
    
    Request Body:
        name: str - Location name
        
    Returns:
        200: Saved status
    """
    try:
        from flask import current_app
        
        data = request.get_json() or {}
        location_name = str(data.get("name", "")).strip()
        
        if not location_name:
            return jsonify({"success": False, "error": "Location name is required"}), 400
        
        user_id = _get_current_user_id()
        
        # Get MongoDB database
        db = current_app.config["APP_MONGO_CLIENT"][current_app.config["APP_MONGO_DBNAME"]]
        
        # Check if location is saved
        saved_location = db.saved_locations.find_one({
            "userId": user_id,
            "name": location_name
        })
        
        return jsonify({
            "success": True,
            "isSaved": saved_location is not None
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking location saved status: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@travel_log_bp.route("/saved", methods=["GET"])
@login_required
def get_saved_locations():
    """
    Get user's saved locations.
    
    Query Parameters:
        page: int - Page number (default: 1)
        limit: int - Items per page (default: 10, max: 50)
        
    Returns:
        200: List of saved locations with pagination
    """
    try:
        from flask import current_app
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # Get MongoDB database
        db = current_app.config["APP_MONGO_CLIENT"][current_app.config["APP_MONGO_DBNAME"]]
        user_id = _get_current_user_id()
        
        # Get saved locations with pagination
        skip = (page - 1) * limit
        saved_locations = list(db.saved_locations.find(
            {"userId": user_id},
            {"_id": 0}  # Exclude MongoDB _id
        ).sort("savedAt", -1).skip(skip).limit(limit))
        
        total = db.saved_locations.count_documents({"userId": user_id})
        
        # Add isSaved flag to all locations
        for loc in saved_locations:
            loc["isSaved"] = True
            # Convert datetime to ISO string
            if "savedAt" in loc and loc["savedAt"]:
                loc["savedAt"] = loc["savedAt"].isoformat()
        
        return jsonify({
            "success": True,
            "locations": saved_locations,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": (total + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting saved locations: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500