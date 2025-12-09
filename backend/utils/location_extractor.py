from __future__ import annotations

import csv
import re
import os
import json
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

# OpenMap.vn Configuration
OPENMAP_BASE_URL = "https://mapapis.openmap.vn/v1"
OPENMAP_API_KEY = os.getenv("OPENMAP_API_KEY")

# Once a 403 occurs, disable all OSM calls for the entire process lifetime
OSM_DISABLED = False


def query_openmap_vn(query: str) -> List[Dict[str, Any]]:
    """
    Query OpenMap.vn Geocoding API.
    Returns a list of results in a standardized format (similar to Nominatim).
    """
    if not OPENMAP_API_KEY:
        return []

    url = f"{OPENMAP_BASE_URL}/geocode/search"
    params = {
        "text": query,
        "apikey": OPENMAP_API_KEY,
    }
    
    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        
        # Parse GeoJSON response from OpenMap.vn
        results = []
        features = data.get("features", [])
        
        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [])
            
            if len(coords) >= 2:
                lng, lat = coords[0], coords[1]
                
                # Normalize to Nominatim structure
                results.append({
                    "lat": str(lat),
                    "lon": str(lng),
                    "display_name": props.get("label") or props.get("name") or props.get("address") or query,
                    "address": {
                        "amenity": props.get("name"),
                        "city": props.get("region"),
                        "country": "Việt Nam"
                    }, 
                    "raw_source": "openmap_vn"
                })
        
        return results

    except Exception as e:
        logger.error(f"[location_extractor][OpenMap] Error: {e}")
        return []


def query_nominatim(query: str) -> List[Dict[str, Any]]:
    """
    Query OpenStreetMap Nominatim API.
    """
    global OSM_DISABLED
    if OSM_DISABLED:
        return []
        
    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 5,
        "addressdetails": 1,
        "email": OSM_EMAIL,
    }
    headers = {"User-Agent": OSM_USER_AGENT}
    
    try:
        resp = requests.get(OSM_SEARCH_URL, params=params, headers=headers, timeout=8)
        
        if resp.status_code == 403:
            logger.error("[location_extractor][OSM] 403 Forbidden. Disabling OSM.")
            OSM_DISABLED = True
            return []
            
        resp.raise_for_status()
        return resp.json()
        
    except Exception as e:
        logger.warning(f"[location_extractor][OSM] Error on '{query}': {e}")
        return []


@lru_cache(maxsize=256)
def search_osm_location(
    name: str,
    context: str = DEFAULT_OSM_CONTEXT,
    region_hint: Optional[str] = None,
    original_name: Optional[str] = None,  # NEW: preserve original name
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
    def _norm(text: str) -> str:
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
            pn = _norm(p)
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

    norm_name = _norm(name)
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
        #   "Vườn hoa thành phố" + "Đà Lạt, Việt Nam"
        if region_hint:
            query_context = f"{region_hint}, {DEFAULT_OSM_CONTEXT}"
        else:
            query_context = context or DEFAULT_OSM_CONTEXT

        query_text = f"{q}, {query_context}" if query_context else q

        # Provider Strategy: OpenMap (Priority) -> Nominatim (Fallback)
        data = []
        source_label = ""

        if OPENMAP_API_KEY:
            data = query_openmap_vn(query_text)
            source_label = "openmap_vn"

        # If OpenMap found nothing (or no key), try Nominatim
        if not data:
            data = query_nominatim(query_text)
            source_label = "osm_fallback"

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
                addr_norm = _norm(addr_text)

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
            "name": original_name or q,  # Use original name if provided
            "address": address,
            "lat": lat,
            "lng": lng,
            "description": None,
            "imageUrl": None,
            "source": source_label
        }



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
      - Location keywords (Chùa, Đền, Bảo tàng, etc.) + proper nouns
      - Standalone proper nouns (2-4 words, capitalized)
      - Quoted location names
      - Numbered list items
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

    # Pattern 3 — Location keywords + proper nouns
    # Matches: "Chùa Ba Vàng", "Quần đảo Hoàng Sa", "Bảo tàng Quang Trung", "Nhà thờ Đức Bà", etc.
    location_keywords = [
        "Chùa", "Đền", "Bảo tàng", "Quần đảo", "Vịnh", "Núi", "Công viên",
        "Khu du lịch", "Phố cổ", "Làng", "Bán đảo", "Đảo", "Hang", "Động",
        "Hồ", "Thác", "Cầu", "Dinh", "Lăng", "Nhà thờ", "Tháp", "Chợ",
        "Đài", "Cung điện", "Thành", "Khu", "Vườn", "Suối", "Biển", "Bãi biển"
    ]
    keyword_pattern = "|".join(location_keywords)
    for m in re.finditer(
        rf"(?:{keyword_pattern})\s+([A-ZĐÂÊÁÀƯƠÔÍÓÚ][A-Za-zÀ-ỹ0-9\s\-\']+?)(?=\s*(?:là|ở|tại|của|và|,|\.|$|thuộc|nằm|\)|\(|;|bạn|nhé|đấy|ạ))",
        answer
    ):
        # Combine keyword + name for full location name
        full_match = m.group(0).strip()
        if full_match and full_match not in candidates:
            candidates.append(full_match)

    # Pattern 4 — Standalone proper nouns (2-4 words, capitalized) WITH CONTEXT
    # Only extract if preceded by location context words or in a list
    # Matches: "đến Hoàng Sa", "tham quan Trường Sa", "ở Tam Cốc"
    location_context_words = r"(?:đến|tham quan|ghé|viếng|ở|tại|nằm ở|thuộc|gần|quanh|vùng|khu vực)"
    
    # Pattern 4a: With location context words
    for m in re.finditer(
        rf"{location_context_words}\s+([A-ZĐÂÊÁÀƯƠÔÍÓÚ][a-zà-ỹ]+(?:\s+[A-ZĐÂÊÁÀƯƠÔÍÓÚ][a-zà-ỹ]+){{1,3}})\b",
        answer
    ):
        name = m.group(1).strip()
        excluded_words = {
            "Việt Nam", "Hà Nội", "Thành Phố", "Quận", "Huyện", "Xã", "Phường",
            "Tỉnh", "Thị Xã", "Đường", "Phố", "Ngày", "Tháng", "Năm",
            "Thành Phố Hồ Chí Minh", "Hồ Chí Minh", "Sài Gòn",
            "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Biên Hòa", "Nha Trang",
            "Huế", "Buôn Ma Thuột", "Quy Nhơn", "Vũng Tàu"
        }
        if name and name not in candidates and name not in excluded_words:
            if not any(name in c for c in candidates):
                candidates.append(name)
    
    # Pattern 4b: In a list with "và" (and)
    # Matches: "Hoàng Sa và Trường Sa"
    for m in re.finditer(
        r"\b([A-ZĐÂÊÁÀƯƠÔÍÓÚ][a-zà-ỹ]+(?:\s+[A-ZĐÂÊÁÀƯƠÔÍÓÚ][a-zà-ỹ]+){1,2})\s+và\s+([A-ZĐÂÊÁÀƯƠÔÍÓÚ][a-zà-ỹ]+(?:\s+[A-ZĐÂÊÁÀƯƠÔÍÓÚ][a-zà-ỹ]+){1,2})\b",
        answer
    ):
        for name in [m.group(1).strip(), m.group(2).strip()]:
            excluded_words = {
                "Việt Nam", "Hà Nội", "Thành Phố", "Quận", "Huyện", "Xã", "Phường",
                "Tỉnh", "Thị Xã", "Đường", "Phố", "Ngày", "Tháng", "Năm",
                "Thành Phố Hồ Chí Minh", "Hồ Chí Minh", "Sài Gòn",
                "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Biên Hòa", "Nha Trang",
                "Huế", "Buôn Ma Thuột", "Quy Nhơn", "Vũng Tàu"
            }
            if name and name not in candidates and name not in excluded_words:
                if not any(name in c for c in candidates):
                    candidates.append(name)

    # Pattern 5 — Quoted location names
    # Matches: "Hoàng Sa", 'Trường Sa'
    for m in re.finditer(r"[\"']([A-ZĐÂÊÁÀƯƠÔÍÓÚ][A-Za-zÀ-ỹ0-9\s\-\']+?)[\"']", answer):
        name = m.group(1).strip()
        if name and name not in candidates:
            candidates.append(name)

    # Pattern 6 — Numbered list items (without colon)
    # Matches: "1. Chùa Ba Vàng", "2) Bảo tàng Quang Trung"
    for m in re.finditer(
        r"^\d+[\.)]\s+([A-ZĐÂÊÁÀƯƠÔÍÓÚ][A-Za-zÀ-ỹ0-9\s\-\',]+?)(?=\s*$|\s*\(|\s*-|\s*:)",
        answer,
        flags=re.MULTILINE
    ):
        name = m.group(1).strip()
        if name and name not in candidates:
            candidates.append(name)

    # Clean overly long “names”
    cleaned = []
    for name in candidates:
        # Optionally strip leading numbering like "1. "
        base_for_len = re.sub(r"^\d+[).\s-]+", "", name).strip()
        # Only check the part before "(" to avoid dropping long formal names
        base_for_len = base_for_len.split("(")[0].strip()

        # Filter criteria
        if len(base_for_len) < 3:  # Too short
            continue
        if len(base_for_len.split()) > 6:  # Too many words (likely a sentence)
            continue
        if len(name) > 80:  # Too long
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

    lat = next(
        (parse_float(row.get(k)) for k in lat_keys if k in row and parse_float(row.get(k)) is not None),
        None,
    )
    lng = next(
        (parse_float(row.get(k)) for k in lng_keys if k in row and parse_float(row.get(k)) is not None),
        None,
    )

    return lat, lng

# ============================================================
# MATCHING LOGIC (CSV)
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
    Match a location name with entries in the CSV.
    
    Matching strategy:
      1. Strict match: All tokens in name must exist in row_name
      2. Flexible match: Remove generic prefixes and try again
      
    This allows matching variations like:
      - "Khu danh thắng Yên Tử" ↔ "Di tích danh thắng Yên Tử"
      - "Khu du lịch Tam Cốc" ↔ "Danh thắng Tam Cốc"
    """
    norm_name = normalize_text(name)
    name_tokens = set(tokenize(name))

    best_row: Optional[Dict[str, str]] = None
    best_score = 0.0
    strict_candidates: List[Dict[str, str]] = []

    # Generic prefixes that can vary between chatbot and CSV
    generic_prefixes = {'khu', 'di', 'tich', 'danh', 'thang', 'du', 'lich', 'khu', 'vung'}

    for row in rows:
        row_name = get_row_name(row)
        if not row_name:
            continue

        row_tokens = set(tokenize(row_name))
        if not row_tokens:
            continue

        # Strategy 1: Strict match - all tokens must exist
        if name_tokens and name_tokens.issubset(row_tokens):
            strict_candidates.append(row)
            continue
        
        # Strategy 2: Flexible match - remove generic prefixes and try again
        # Get core tokens (non-generic)
        name_core_tokens = name_tokens - generic_prefixes
        row_core_tokens = row_tokens - generic_prefixes
        
        # If core tokens match well (at least 80% overlap), consider it a match
        if name_core_tokens and row_core_tokens:
            overlap = len(name_core_tokens & row_core_tokens)
            min_overlap = min(len(name_core_tokens), len(row_core_tokens))
            
            if overlap >= min_overlap * 0.8:  # 80% of core tokens match
                strict_candidates.append(row)

    if not strict_candidates:
        return None

    # Among candidates, choose best fuzzy score
    for row in strict_candidates:
        row_name = get_row_name(row)
        score = SequenceMatcher(
            None, norm_name, normalize_text(row_name)
        ).ratio()
        if score > best_score:
            best_score = score
            best_row = row

    if best_row:
        # If only one candidate, trust it even if score is low
        if len(strict_candidates) == 1:
            return best_row
        # Otherwise require min_score
        if best_score >= min_score:
            return best_row

    return None

# ============================================================
# REGION HINT EXTRACTION
# ============================================================

def extract_region_hint_province(answer: str) -> Optional[str]:
    """
    Try to extract a province/city name from the chatbot answer by scanning:
      - 63 Vietnamese provinces
      - A curated list of major tourism cities (Đà Lạt, Nha Trang, Hội An, ...)
      - Common synonyms (Sài Gòn -> TP.HCM, ...)
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

# ============================================================
# ADDRESS HEURISTIC + SINGLE-NAME RESOLVER
# ============================================================

def looks_like_address(query: str) -> bool:
    """
    Heuristic check to decide if the user input looks more like a full address
    than a landmark name.

    We treat it as an address if:
      - It contains digits (house number), OR
      - It contains typical street/ward/city tokens.
    """
    if not query:
        return False

    q = query.lower()

    # If there is at least one digit, it is very likely a street address
    if any(ch.isdigit() for ch in q):
        return True

    # Exception: "Phố cổ" (Old Quarter) is a landmark, not necessarily an address
    if "phố cổ" in q or "pho co" in q:
        return False

    street_keywords = [
        "đường", "duong",
        "phố", "pho",
        "street", "st.",
        "phường", "phuong",
        "quận", "quan",
        "thành phố", "tp.", "tp ",
        "city", "ward", "district",
    ]

    return any(kw in q for kw in street_keywords)


def resolve_location_by_name(
    name: str,
    context_answer: Optional[str] = None,
) -> Optional[Dict[str, object]]:
    """
    Resolve a single location name or address using:
      1. CSV strict match (for landmark names inside our curated dataset).
      2. OSM fallback (for both names and raw addresses).

    If the input looks like a full address (e.g. contains house number,
    street name, ward/district keywords), we skip CSV and go directly to OSM.
    """
    if not name:
        return None

    # Address-like input → skip CSV and resolve directly via OSM
    if looks_like_address(name):
        # Try to extract region hint from the whole string or context
        region_hint = extract_region_hint_province(context_answer or name)

        if region_hint:
            logger.info(
                f"[location_extractor][OSM] Address-like input with region hint "
                f"'{region_hint}' for '{name}'"
            )

        return search_osm_location(
            name,
            context=DEFAULT_OSM_CONTEXT,
            region_hint=region_hint,
            original_name=name,  # Preserve original name
        )

    # Otherwise treat input as a landmark name and use CSV first
    rows = load_locations()

    csv_row = find_best_match(name, rows, min_score=0.5)
    if csv_row:
        lat, lng = get_lat_lng(csv_row)
        if lat is not None and lng is not None:
            return {
                "name": get_row_name(csv_row),
                "address": csv_row.get("DiaChi", "") or "",
                "lat": lat,
                "lng": lng,
                "description": csv_row.get("NoiDung") or "",
                "imageUrl": (
                    csv_row.get("ImageURL")
                    if csv_row.get("ImageURL") not in (None, "", "N/A")
                    else None
                ),
                "source": "csv",
            }

    # CSV failed or missing lat/lng → OSM fallback
    if context_answer:
        region_hint = extract_region_hint_province(context_answer)
    else:
        region_hint = extract_region_hint_province(name)

    if region_hint:
        logger.info(
            f"[location_extractor][OSM] Using region hint '{region_hint}' "
            f"for direct name '{name}'"
        )

    return search_osm_location(
        name,
        context=DEFAULT_OSM_CONTEXT,
        region_hint=region_hint,
        original_name=name,  # Preserve original candidate name
    )

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
      2. Fallback to OpenStreetMap Nominatim (region-aware, if possible)
    
    Smart filtering:
      - Prioritizes specific landmarks over generic city names
      - For single-location responses (e.g., landmark recognition), returns only the primary location
    """
    # Warm CSV cache (resolve_location_by_name also uses it)
    _ = load_locations()

    names = extract_candidate_names(answer)
    logger.info(f"[location_extractor] Candidate names: {names}")

    matched: List[Dict[str, object]] = []
    seen_names = set()

    for name in names:
        # Use the shared resolver for consistency between phases
        location_data = resolve_location_by_name(name, context_answer=answer)

        if location_data:
            resolved_name = location_data.get("name") or name
            if resolved_name not in seen_names:
                seen_names.add(resolved_name)
                # Track the original candidate name for filtering
                location_data["_original_candidate"] = name
                matched.append(location_data)

    # Smart filtering: Remove generic city names if specific landmarks are present
    if len(matched) > 1:
        # Generic location patterns to filter out when specific landmarks exist
        generic_patterns = [
            "Thành phố Hồ Chí Minh", "Hồ Chí Minh", "Sài Gòn",
            "Hà Nội", "Đà Nẵng", "Hải Phòng", "Cần Thơ",
            "Biên Hòa", "Nha Trang", "Huế", "Buôn Ma Thuột", 
            "Quy Nhơn", "Vũng Tàu", "Đà Lạt", "Hội An"
        ]
        
        landmark_keywords = [
            "Chùa", "Đền", "Bảo tàng", "Nhà thờ", "Dinh", "Lăng", 
            "Tháp", "Cung điện", "Phố cổ", "Chợ", "Vịnh", "Hang", "Động"
        ]
        
        # Debug: Log original candidates
        logger.info(f"[location_extractor] Checking {len(matched)} locations for filtering:")
        for loc in matched:
            orig = loc.get("_original_candidate", "N/A")
            name = loc.get("name", "N/A")
            logger.info(f"  - Original: '{orig}' → Resolved: '{name}'")
        
        # Check if we have locations with landmark keywords in ORIGINAL candidates
        has_landmark_keyword = any(
            any(keyword in loc.get("_original_candidate", "") for keyword in landmark_keywords)
            for loc in matched
        )
        
        logger.info(f"[location_extractor] has_landmark_keyword = {has_landmark_keyword}")
        
        if has_landmark_keyword:
            # Filter out locations from generic candidates (check ONLY original candidate)
            filtered = []
            for loc in matched:
                original_candidate = loc.get("_original_candidate", "")
                
                # First check if original candidate has landmark keyword
                has_keyword = any(kw in original_candidate for kw in landmark_keywords)
                
                # If it has a landmark keyword, keep it (even if it contains city name)
                if has_keyword:
                    filtered.append(loc)
                    continue
                
                # If no landmark keyword, check if it's a generic city name
                is_generic = False
                for pattern in generic_patterns:
                    if pattern.lower() in original_candidate.lower() or original_candidate.lower() in pattern.lower():
                        is_generic = True
                        logger.info(f"[location_extractor] Filtering out '{original_candidate}' (generic city, no landmark keyword)")
                        break
                
                # Keep only if not generic
                if not is_generic:
                    filtered.append(loc)
            
            if filtered:  # Only use filtered list if it's not empty
                matched = filtered
                logger.info(f"[location_extractor] After filtering: {len(matched)} specific locations remain")

    # Clean up internal tracking field before returning
    for loc in matched:
        loc.pop("_original_candidate", None)

    logger.info(f"[location_extractor] Matched {len(matched)} locations (csv+osm)")
    return matched
