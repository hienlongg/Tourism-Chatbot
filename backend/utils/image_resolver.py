from __future__ import annotations
import os
import requests
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"


def fetch_image_from_google(name: str) -> Optional[str]:
    """
    Fetch an image using Google Custom Search Engine.
    Works for locations, addresses, landmarks.
    """
    # Read values from .env
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_CSE_CX")

    if not api_key or not cx:
        logger.warning("[image_resolver] Missing GOOGLE_SEARCH_API_KEY or GOOGLE_CSE_CX")
        return None

    try:
        resp = requests.get(
            GOOGLE_CSE_URL,
            params={
                "key": api_key,
                "cx": cx,
                "q": name,
                "searchType": "image",
                "num": 1,
                "safe": "active",
            },
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()

        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["link"]

    except Exception as e:
        logger.warning(f"[image_resolver] Google CSE error for '{name}': {e}")

    return None

def enrich_location_with_image(location: Dict[str, object]) -> Dict[str, object]:
    """
    If the location already has an image (CSV), keep it.
    Otherwise fetch from Google Search.
    """
    if not location:
        return location

    # Already has image from CSV
    if location.get("imageUrl"):
        return location

    name = str(location.get("name", "")).strip()
    if not name:
        return location

    img = fetch_image_from_google(name)
    if img:
        location["imageUrl"] = img

    return location
