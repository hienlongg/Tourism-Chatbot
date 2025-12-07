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

VIETNAM_PROVINCES = [
    "An Giang",
    "Bà Rịa - Vũng Tàu",
    "Bạc Liêu",
    "Bắc Giang",
    "Bắc Kạn",
    "Bắc Ninh",
    "Bến Tre",
    "Bình Dương",
    "Bình Định",
    "Bình Phước",
    "Bình Thuận",
    "Cà Mau",
    "Cao Bằng",
    "Cần Thơ",
    "Đà Nẵng",
    "Đắk Lắk",
    "Đắk Nông",
    "Điện Biên",
    "Đồng Nai",
    "Đồng Tháp",
    "Gia Lai",
    "Hà Giang",
    "Hà Nam",
    "Hà Nội",
    "Hà Tĩnh",
    "Hải Dương",
    "Hải Phòng",
    "Hậu Giang",
    "Hòa Bình",
    "Hưng Yên",
    "Khánh Hòa",
    "Kiên Giang",
    "Kon Tum",
    "Lai Châu",
    "Lạng Sơn",
    "Lào Cai",
    "Lâm Đồng",
    "Long An",
    "Nam Định",
    "Nghệ An",
    "Ninh Bình",
    "Ninh Thuận",
    "Phú Thọ",
    "Phú Yên",
    "Quảng Bình",
    "Quảng Nam",
    "Quảng Ngãi",
    "Quảng Ninh",
    "Quảng Trị",
    "Sóc Trăng",
    "Sơn La",
    "Tây Ninh",
    "Thái Bình",
    "Thái Nguyên",
    "Thanh Hóa",
    "Thừa Thiên Huế",
    "Tiền Giang",
    "Thành phố Hồ Chí Minh",
    "Trà Vinh",
    "Tuyên Quang",
    "Vĩnh Long",
    "Vĩnh Phúc",
    "Yên Bái",
]

PROVINCE_SYNONYMS = {
    "Sài Gòn": "Thành phố Hồ Chí Minh",
    "TP Hồ Chí Minh": "Thành phố Hồ Chí Minh",
    "TP. Hồ Chí Minh": "Thành phố Hồ Chí Minh",
    "TP HCM": "Thành phố Hồ Chí Minh",
    "HCM": "Thành phố Hồ Chí Minh",
    "Vũng Tàu": "Bà Rịa - Vũng Tàu",
    "BRVT": "Bà Rịa - Vũng Tàu",
}

VIETNAM_TOURISM_CITIES = [
    "Đà Lạt",
    "Nha Trang",
    "Hội An",
    "Huế",
    "Sa Pa",
    "Phan Thiết",
    "Phú Quốc",
    "Vũng Tàu",
    "Đà Nẵng",  
    "Hạ Long",
]

# ============================================================
# LOAD CSV INTO MEMORY (cached)
# ============================================================

@lru_cache(maxsize=1)
def load_locations() -> List[Dict[str, str]]:
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
def search_osm_location(
    name: str,
    context: str = DEFAULT_OSM_CONTEXT,
    region_hint: Optional[str] = None,
) -> Optional[Dict[str, object]]:
    """
    Perform a structured search on the OpenStreetMap Nominatim API to resolve a
    location name. This function uses multiple fallback strategies in order to
    increase accuracy when dealing with noisy or ambiguous names.

    Resolution strategy:
      1. Query the raw name directly.
      2. Remove common prefixes (e.g. "Khu du lịch", "Chùa", "Đền", etc.) and retry.
      3. Generate split variants (e.g. "Tam Cốc - Bích Động" → "Tam Cốc").

    Region-aware filtering:
      If `region_hint` is provided (e.g., "Đà Lạt, Lâm Đồng"), the function:
        - Appends this hint into the query text to improve search relevance.
        - Expands the returned result set (limit=5) and performs a strict filter:
              Every normalized component of the region_hint MUST appear
              in the item's address or display_name.
        - This prevents mismatches such as:
              “Vườn Hoa Thành Phố” in Đà Lạt incorrectly resolving to Tây Ninh.

    Returns:
        A dictionary with resolved location data:
            {
                "name": <string>,
                "address": <string>,
                "lat": <float>,
                "lng": <float>,
                "description": None,
                "imageUrl": None,
                "source": "osm_fallback"
            }
        Or None if no valid match is found.
    """

    global OSM_DISABLED
    if OSM_DISABLED:
        return None

    # -----------------------------
    # Helper: normalize a string by
    # removing accents + lowercasing
    # -----------------------------
    def normalize(text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFD", text)
        text = "".join(c for c in text if unicodedata.category(c) != "Mn")
        return text.lower().strip()

    # ----------------------------------------------------------------------
    # Normalize the region hint into searchable components
    # Example: "Đà Lạt, Lâm Đồng" → ["da lat", "lam dong"]
    # These are later used for strict filtering against OSM address fields.
    # ----------------------------------------------------------------------
    region_parts_norm: List[str] = []
    if region_hint:
        raw_parts = re.split(r"[,/|-]", region_hint)
        for part in raw_parts:
            p = part.strip()
            if len(p) < 2:
                continue
            pn = normalize(p)
            if pn in ("viet nam",):
                continue
            region_parts_norm.append(pn)

    # -----------------------------------------
    # Generate all fallback name variants
    # -----------------------------------------
    queries: List[str] = []
    queries.append(name)  # raw name

    # Remove known prefixes (e.g. "Chùa", "Đền", "Khu du lịch") to make queries cleaner
    prefixes = [
        "khu du lich","quan the","danh thang","di tich","vuon quoc gia",
        "khu bao ton","trung tam","quang truong","pho co","nha tho",
        "chua","den","lang","ban","dong","hang","vinh","cong vien"
    ]

    norm_name = normalize(name)
    for prefix in prefixes:
        if norm_name.startswith(prefix + " "):
            cleaned = name[len(prefix) + 1:].strip()
            queries.append(cleaned)
            break

    # Split variants: "A - B" → "A", "A, B" → "A"
    if " - " in name:
        queries.append(name.split(" - ")[0].strip())
    if "-" in name:
        queries.append(name.split("-")[0].strip())
    if "," in name:
        queries.append(name.split(",")[0].strip())

    # Ensure uniqueness
    queries = list(dict.fromkeys(queries))

    headers = {"User-Agent": OSM_USER_AGENT}

    # ----------------------------------------------------------------------
    # Try each variant until a region-valid match is found
    # ----------------------------------------------------------------------
    for q in queries:
        if len(q) < 3:
            continue

        # If region_hint is present, embed it directly into the query context
        # Example:
        #   "Vườn hoa thành phố" + "Đà Lạt, Lâm Đồng, Việt Nam"
        if region_hint:
            query_context = f"{region_hint}, {DEFAULT_OSM_CONTEXT}"
        else:
            query_context = context or DEFAULT_OSM_CONTEXT

        query_text = f"{q}, {query_context}" if query_context else q

        params = {
            "q": query_text,
            "format": "jsonv2",
            "limit": 5,
            "addressdetails": 1,
            "email": OSM_EMAIL,
        }

        try:
            resp = requests.get(OSM_SEARCH_URL, params=params, headers=headers, timeout=8)

            # If Nominatim blocks us (403), disable OSM entirely
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

            # ----------------------------------------------------------------------
            # Region-aware filtering:
            # Among all returned items, pick the first one whose address contains
            # ALL region components (if region_hint is provided).
            # ----------------------------------------------------------------------
            chosen_item = None

            for item in data:
                lat = parse_float(item.get("lat"))
                lng = parse_float(item.get("lon"))
                if lat is None or lng is None:
                    continue

                if region_parts_norm:
                    addr = item.get("address", {}) or {}
                    display = item.get("display_name", "") or ""

                    # Combine all address fields into a single text blob
                    addr_text = " ".join([display] + [str(v) for v in addr.values() if v])
                    addr_norm = normalize(addr_text)

                    # Every part of region_hint must appear in the address
                    if not all(rp in addr_norm for rp in region_parts_norm):
                        continue  # wrong province/city → skip

                chosen_item = item
                break  # valid match found

            if not chosen_item:
                # No item satisfied the region filter — try next fallback query
                continue

            lat = parse_float(chosen_item.get("lat"))
            lng = parse_float(chosen_item.get("lon"))
            address = chosen_item.get("display_name", "") or ""

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

    # No valid result found
    return None

# ============================================================
# TEXT NORMALIZATION HELPERS
# ============================================================

def normalize_text(s: str) -> str:
    """Normalize text: lowercase, remove accents, keep only alphanumerics."""
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # remove accents
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def normalize_for_match(s: str) -> str:
    """
    Normalize text for loose substring matching:
    - lowercase
    - remove Vietnamese accents
    """
    if not s:
        return ""
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def tokenize(s: str) -> List[str]:
    return normalize_text(s).split()


def extract_candidate_names(answer: str) -> List[str]:
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
        if len(name.split()) > 20:
            continue
        if len(name) > 60:
            continue
        cleaned.append(name)

    return cleaned


def parse_float(value: Any) -> Optional[float]:
    """Convert string to float (supports comma decimal separators)."""
    if value is None:
        return None
    s = str(value).strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def get_lat_lng(row: Dict[str, str]) -> (Optional[float], Optional[float]):
    """Retrieve latitude and longitude from multiple possible column names."""
    lat_keys = ["lat", "Lat", "LAT", "latitude", "Latitude", "LATITUDE"]
    lng_keys = ["lng", "Lng", "lon", "Lon", "LON", "long", "Long", "longitude", "Longitude"]

    lat = next(( parse_float(row.get(k)) for k in lat_keys if k in row and parse_float(row.get(k)) is not None ), None)
    lng = next(( parse_float(row.get(k)) for k in lng_keys if k in row and parse_float(row.get(k)) is not None ), None)

    return lat, lng

# ============================================================
# MATCHING LOGIC
# ============================================================

def get_row_name(row: Dict[str, str]) -> str:
    """Return the first available name column in priority order."""
    for col in NAME_COLUMNS:
        if row.get(col):
            return row[col]
    return ""


def find_best_match(
    name: str, rows: List[Dict[str, str]], min_score: float = 0.75
) -> Optional[Dict[str, str]]:
    """
    Strict match a location name with entries in the CSV.

    Rule:
      - Only consider rows whose token set fully contains all tokens from `name`.
      - Among those candidates, pick the one with highest similarity.
      - If no such candidate exists, return None (so we can fallback to OSM).
    """
    norm_name = normalize_text(name)
    name_tokens = set(tokenize(name))

    best_row: Optional[Dict[str, str]] = None
    best_score = 0.0

    # Strict candidates – row must contain ALL tokens in the query
    strict_candidates: List[Dict[str, str]] = []

    for row in rows:
        row_name = get_row_name(row)
        if not row_name:
            continue

        row_tokens = set(tokenize(row_name))
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
        row_name = get_row_name(row)
        score = SequenceMatcher(
            None, norm_name, normalize_text(row_name)
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

def extract_region_hint_province(answer: str) -> Optional[str]:
    """
    Try to extract a province/city name from the chatbot answer by scanning:
      - 63 Vietnamese provinces
      - A curated list of major tourism cities (Đà Lạt, Nha Trang, Hội An, ...)
    """
    if not answer:
        return None

    text_norm = normalize_for_match(answer)

    # 1) Check official province names
    for prov in VIETNAM_PROVINCES:
        prov_norm = normalize_for_match(prov)
        if prov_norm and prov_norm in text_norm:
            return prov

    # 2) Check synonyms for provinces (Sài Gòn → TP.HCM, ...)
    for alias, canonical in PROVINCE_SYNONYMS.items():
        alias_norm = normalize_for_match(alias)
        if alias_norm and alias_norm in text_norm:
            return canonical

    # 3) Check famous tourism cities (Đà Lạt, Nha Trang, Hội An, ...)
    for city in VIETNAM_TOURISM_CITIES:
        city_norm = normalize_for_match(city)
        if city_norm and city_norm in text_norm:
            return city  

    return None

def extract_locations_from_answer(answer: str) -> List[Dict[str, object]]:
    """
    Extract all location objects from the chatbot answer.
    Priority:
      1. Match from CSV dataset (preferred because curated)
      2. Fallback to OpenStreetMap Nominatim
    """
    rows = load_locations()

    names = extract_candidate_names(answer)
    logger.info(f"[location_extractor] Candidate names: {names}")

    matched = []
    seen_names = set()

    for name in names:
        # Try CSV first
        best = find_best_match(name, rows, min_score=0.5)
        location_data = None

        if best:
            resolved_name = get_row_name(best)
            if resolved_name not in seen_names:
                lat, lng = get_lat_lng(best)

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

                # CSV failed → use OSM fallback (with province-level region hint)
        if location_data is None:
            # Global province from the whole answer/question (63 provinces)
            region_hint = extract_region_hint_province(answer)

            if region_hint:
                logger.info(
                    f"[location_extractor][OSM] Using region hint '{region_hint}' for '{name}'"
                )

            osm = search_osm_location(
                name,
                context=DEFAULT_OSM_CONTEXT,
                region_hint=region_hint,
            )

            if osm:
                if osm["name"] not in seen_names:
                    seen_names.add(osm["name"])
                    location_data = osm

        if location_data:
            matched.append(location_data)

    logger.info(f"[location_extractor] Matched {len(matched)} locations (csv+osm)")
    return matched
