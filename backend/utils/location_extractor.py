from __future__ import annotations
import csv
import re
import unicodedata
from pathlib import Path
from functools import lru_cache
from difflib import SequenceMatcher
from typing import List, Dict, Optional, Any
import logging
import requests

logger = logging.getLogger(__name__)

# ============================================================
# CSV DATASET LOCATION
# ============================================================

CSV_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "data"
    / "processed"
    / "danh_sach_thong_tin_dia_danh_chi_tiet.csv"
)

# Possible columns that may contain the name of the landmark
NAME_COLUMNS = ["TenDiaDanh", "enDiaDanh", "DiaDanh"]

# ============================================================
# LOAD CSV INTO MEMORY (cached)
# ============================================================

@lru_cache(maxsize=1)
def _load_locations() -> List[Dict[str, str]]:
    """
    Load the entire CSV file into memory and normalize column names.
    This runs only once due to caching.
    """
    rows: List[Dict[str, str]] = []
    try:
        with CSV_PATH.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize the header keys (strip accidental spaces)
                clean_row = {(k or "").strip(): v for k, v in row.items()}
                rows.append(clean_row)

        logger.info(f"[location_extractor] Loaded {len(rows)} rows from {CSV_PATH}")

    except FileNotFoundError as e:
        logger.error(f"[location_extractor] CSV not found at {CSV_PATH}: {e}")
        raise

    return rows

# ============================================================
# OPENSTREETMAP FALLBACK (Nominatim)
# ============================================================

OSM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
DEFAULT_OSM_CONTEXT = "Việt Nam"
OSM_USER_AGENT = "voyaiage-tourism-chatbot/1.0 (contact: nchin3107@gmail.com)"
OSM_EMAIL = "nchin3107@gmail.com"

# Once a 403 occurs, disable all OSM calls for the entire process lifetime
OSM_DISABLED = False

@lru_cache(maxsize=256)
def _search_osm_location(name: str, context: str = DEFAULT_OSM_CONTEXT) -> Optional[Dict[str, object]]:
    """
    Search a location in OSM using multi-query fallback strategies.
    Strategy order:
      1. Direct query
      2. Cleaned name (remove prefixes)
      3. Split variants (Tam Cốc - Bích Động -> Tam Cốc)
    """

    global OSM_DISABLED
    if OSM_DISABLED:
        return None

    def normalize(text: str) -> str:
        text = unicodedata.normalize("NFD", text)
        return "".join(c for c in text if unicodedata.category(c) != "Mn").lower()

    # 1) Generate all fallback queries
    queries = []

    # Base direct query
    queries.append(name)

    # Prefix cleaning
    prefixes = [
        "khu du lich","quan the","danh thang","di tich","vuon quoc gia",
        "khu bao ton","trung tam","quang truong","pho co","nha tho",
        "chua","den","lang","ban","dong","hang","vinh","cong vien"
    ]

    norm = normalize(name)
    for prefix in prefixes:
        if norm.startswith(prefix + " "):
            cleaned = name[len(prefix) + 1:].strip()
            queries.append(cleaned)
            break

    # Splitting
    if " - " in name:
        queries.append(name.split(" - ")[0].strip())
    if "-" in name:
        queries.append(name.split("-")[0].strip())
    if "," in name:
        queries.append(name.split(",")[0].strip())

    # Remove duplicates
    queries = list(dict.fromkeys(queries))

    headers = {"User-Agent": OSM_USER_AGENT}

    # Try each query until one succeeds
    for q in queries:
        if len(q) < 3:
            continue

        query_text = f"{q}, {context}" if context else q
        params = {
            "q": query_text,
            "format": "jsonv2",
            "limit": 1,
            "addressdetails": 1,
            "email": OSM_EMAIL,
        }

        try:
            resp = requests.get(OSM_SEARCH_URL, params=params, headers=headers, timeout=8)

            # Disabled due to 403
            if resp.status_code == 403:
                logger.warning(
                    f"[location_extractor][OSM] 403 Forbidden for '{query_text}'. Disabling OSM."
                )
                OSM_DISABLED = True
                return None

            if resp.status_code != 200:
                continue

            data = resp.json()
            if not data:
                continue

            item = data[0]
            lat = _parse_float(item.get("lat"))
            lng = _parse_float(item.get("lon"))

            if lat is None or lng is None:
                continue

            address = item.get("display_name", "")

            logger.info(
                f"[location_extractor][OSM] Matched fallback '{q}' → '{address}' (lat={lat}, lng={lng})"
            )

            return {
                "name": q,
                "address": address,
                "lat": lat,
                "lng": lng,
                "description": None,
                "imageUrl": None,
                "source": "osm_fallback"
            }

        except Exception as e:
            logger.warning(f"[location_extractor][OSM] Error on '{q}': {e}")
            continue

    return None

# ============================================================
# TEXT NORMALIZATION HELPERS
# ============================================================

def _normalize_text(s: str) -> str:
    """Normalize text: lowercase, remove accents, keep only alphanumerics."""
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # remove accents
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _tokenize(s: str) -> List[str]:
    return _normalize_text(s).split()


def _extract_candidate_names(answer: str) -> List[str]:
    """
    Extract location names from chatbot output.
    Supports:
      - Markdown bold (**Name**)
      - Lines starting with "Name:"
    """
    candidates: List[str] = []

    # Pattern 1 — Markdown bold
    for m in re.finditer(r"\*\*(.+?)\*\*", answer):
        name = m.group(1).strip().rstrip(":")
        if name and name not in candidates:
            candidates.append(name)

    # Pattern 2 — Lines like "Name:"
    for m in re.finditer(
        r"^[-*]?\s*([A-ZĐÂÊÁÀƯƠÔÍÓÚ][A-Za-zÀ-ỹ0-9\s\-\’’,.]+?)\s*:",
        answer,
        flags=re.MULTILINE,
    ):
        name = m.group(1).strip()
        if name and name not in candidates:
            candidates.append(name)

    # Clean overly long “names”
    cleaned = []
    for name in candidates:
        if len(name.split()) > 8:
            continue
        if len(name) > 60:
            continue
        cleaned.append(name)

    return cleaned


def _parse_float(value: Any) -> Optional[float]:
    """Convert string to float (supports comma decimal separators)."""
    if value is None:
        return None
    s = str(value).strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _get_lat_lng(row: Dict[str, str]) -> (Optional[float], Optional[float]):
    """Retrieve latitude and longitude from multiple possible column names."""
    lat_keys = ["lat", "Lat", "LAT", "latitude", "Latitude", "LATITUDE"]
    lng_keys = ["lng", "Lng", "lon", "Lon", "LON", "long", "Long", "longitude", "Longitude"]

    lat = next(( _parse_float(row.get(k)) for k in lat_keys if k in row and _parse_float(row.get(k)) is not None ), None)
    lng = next(( _parse_float(row.get(k)) for k in lng_keys if k in row and _parse_float(row.get(k)) is not None ), None)

    return lat, lng

# ============================================================
# MATCHING LOGIC
# ============================================================

def _get_row_name(row: Dict[str, str]) -> str:
    """Return the first available name column in priority order."""
    for col in NAME_COLUMNS:
        if row.get(col):
            return row[col]
    return ""


def _find_best_match(
    name: str, rows: List[Dict[str, str]], min_score: float = 0.75
) -> Optional[Dict[str, str]]:
    """
    Strict match a location name with entries in the CSV.

    Rule:
      - Only consider rows whose token set fully contains all tokens from `name`.
      - Among those candidates, pick the one with highest similarity.
      - If no such candidate exists, return None (so we can fallback to OSM).
    """
    norm_name = _normalize_text(name)
    name_tokens = set(_tokenize(name))

    best_row: Optional[Dict[str, str]] = None
    best_score = 0.0

    # Strict candidates – row must contain ALL tokens in the query
    strict_candidates: List[Dict[str, str]] = []

    for row in rows:
        row_name = _get_row_name(row)
        if not row_name:
            continue

        row_tokens = set(_tokenize(row_name))
        if not row_tokens:
            continue

        # All tokens in name must exist in row_name
        if name_tokens and name_tokens.issubset(row_tokens):
            strict_candidates.append(row)

    # If we have no strict candidates -> treat as "not found in CSV"
    if not strict_candidates:
        return None

    # Among strict candidates, choose best fuzzy score
    for row in strict_candidates:
        row_name = _get_row_name(row)
        score = SequenceMatcher(
            None, norm_name, _normalize_text(row_name)
        ).ratio()
        if score > best_score:
            best_score = score
            best_row = row

    if best_row and best_score >= min_score:
        return best_row
    return None

# ============================================================
# MAIN PUBLIC FUNCTION
# ============================================================

def extract_locations_from_answer(answer: str) -> List[Dict[str, object]]:
    """
    Extract all location objects from the chatbot answer.
    Priority:
      1. Match from CSV dataset (preferred because curated)
      2. Fallback to OpenStreetMap Nominatim
    """
    rows = _load_locations()

    names = _extract_candidate_names(answer)
    logger.info(f"[location_extractor] Candidate names: {names}")

    matched = []
    seen_names = set()

    for name in names:
        # Try CSV first
        best = _find_best_match(name, rows, min_score=0.8)
        location_data = None

        if best:
            resolved_name = _get_row_name(best)
            if resolved_name not in seen_names:
                lat, lng = _get_lat_lng(best)

                if lat is not None and lng is not None:
                    seen_names.add(resolved_name)
                    location_data = {
                        "name": resolved_name,
                        "address": best.get("DiaChi", "") or "",
                        "lat": lat,
                        "lng": lng,
                        "description": best.get("NoiDung") or "",
                        "imageUrl": (
                            best.get("ImageURL")
                            if best.get("ImageURL") not in (None, "", "N/A")
                            else None
                        ),
                        "source": "csv",
                    }
                else:
                    logger.warning(
                        f"[location_extractor] CSV row matched '{resolved_name}' but missing valid lat/lng"
                    )

        # CSV failed → use OSM fallback
        if location_data is None:
            osm = _search_osm_location(name)
            if osm:
                if osm["name"] not in seen_names:
                    seen_names.add(osm["name"])
                    location_data = osm

        if location_data:
            matched.append(location_data)

    logger.info(f"[location_extractor] Matched {len(matched)} locations (csv+osm)")
    return matched
