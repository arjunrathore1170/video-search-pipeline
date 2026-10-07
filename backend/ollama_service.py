"""
Ollama / Llama 3 Intent Extraction Service
-------------------------------------------
Sends the user's natural-language query to a local Ollama instance
running Llama 3 / Llama 3.2 and parses the structured JSON intent.

Falls back to a keyword-based mock extractor when Ollama is
unreachable or returns invalid output.
"""

import json
import re
import requests

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
DEFAULT_MODELS = ["llama3.2:1b", "llama3.2", "llama3", "llama3.2:latest", "llama3:latest", "tinyllama"]

SYSTEM_PROMPT = """You are a video search intent extraction system.

Convert the user's natural language query into structured JSON.

Extract only information explicitly present in the query.

Possible fields:
- object_type: "person" or "vehicle" or specific type like "car", "truck"
- shirt: color of the shirt (for persons)
- pants: color of the pants (for persons)
- vehicle_type: "car", "truck", "motorcycle", "bus", etc.
- vehicle_color: color of the vehicle
- camera_id: camera identifier (numeric like 1, or string like "CAM_01")
- camera_name: camera location name like "Front Gate", "Room", "Parking"
- time_after: time in HH:MM format (24-hour)
- time_before: time in HH:MM format (24-hour)

Return ONLY valid JSON. No explanations, no markdown, no extra text.

Examples:

User: Show the person wearing a red shirt after 10 PM.
Output: {"object_type": "person", "shirt": "red", "time_after": "22:00"}

User: Find vehicles in camera 2 before 9 PM.
Output: {"object_type": "vehicle", "camera_id": "CAM_02", "time_before": "21:00"}

User: Show a person with blue pants and white shirt.
Output: {"object_type": "person", "shirt": "white", "pants": "blue"}

User: Show me the person near the front gate wearing a red shirt.
Output: {"object_type": "person", "camera_name": "Front Gate", "shirt": "red"}

User: Find person in the room.
Output: {"object_type": "person", "camera_name": "Room"}
"""


def get_active_model() -> str | None:
    """Fetch installed models from Ollama tags API and return the best available model."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            installed = [m.get("name") for m in data.get("models", [])]
            for target in DEFAULT_MODELS:
                for inst in installed:
                    if inst == target or inst.startswith(target + ":"):
                        return inst
            if installed:
                return installed[0]
    except Exception:
        pass
    return None


def extract_intent(query: str) -> tuple[dict, bool]:
    """Try Ollama first if model is active; fall back to mock extraction on failure.

    Returns a tuple: (intent_dict, used_fallback: bool)
    """
    model = get_active_model()
    if model:
        try:
            intent = _ollama_extract(query, model)
            return intent, False
        except Exception:
            pass
    
    intent = mock_extract_intent(query)
    return intent, True


def _ollama_extract(query: str, model: str) -> dict:
    """Call Ollama's generate endpoint and parse the JSON response."""
    payload = {
        "model": model,
        "prompt": f"User: {query}\nOutput:",
        "system": SYSTEM_PROMPT,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1,
        },
    }

    resp = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=5)
    resp.raise_for_status()

    raw = resp.json().get("response", "").strip()

    # Try to extract JSON from the response (handle markdown fences)
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not json_match:
        raise ValueError(f"No JSON object found in Ollama response: {raw}")

    intent = json.loads(json_match.group())

    # Validate – must be a dict
    if not isinstance(intent, dict):
        raise ValueError("Ollama returned non-dict JSON")

    return intent


# ── Keyword-based fallback ──────────────────────────────────────


# Color list used for matching
_COLORS = [
    "red", "blue", "green", "yellow", "white", "black",
    "gray", "grey", "orange", "purple", "pink", "brown", "silver",
]

# Time patterns: "10 PM", "10PM", "10:30 PM", "22:00"
_TIME_RE = re.compile(
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)", re.IGNORECASE
)
_TIME_24_RE = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")

# Camera pattern: "camera 1", "cam 01", "CAM_02"
_CAM_RE = re.compile(
    r"(?:camera|cam)[_\s]*(\d{1,2})", re.IGNORECASE
)


def _parse_time(text: str) -> str | None:
    """Return HH:MM from natural language time or None."""
    m = _TIME_RE.search(text)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        period = m.group(3).upper()
        if period == "PM" and hour != 12:
            hour += 12
        elif period == "AM" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"

    m24 = _TIME_24_RE.search(text)
    if m24:
        return f"{int(m24.group(1)):02d}:{int(m24.group(2)):02d}"

    return None


def mock_extract_intent(query: str) -> dict:
    """Rule-based intent extraction used as fallback.

    Parses keywords for object type, colors, camera, and time.
    """
    q = query.lower()
    intent: dict = {}

    # ── Object type ──
    vehicle_keywords = ["vehicle", "car", "truck", "motorcycle", "bus", "bike"]
    is_vehicle = any(kw in q for kw in vehicle_keywords)
    is_person = any(kw in q for kw in ["person", "man", "woman", "people", "someone", "guy"])

    if is_vehicle and not is_person:
        intent["object_type"] = "vehicle"
    elif is_person:
        intent["object_type"] = "person"

    # ── Clothing (person) ──
    if intent.get("object_type") == "person" or (not is_vehicle):
        # shirt color
        shirt_match = re.search(
            r"(?:wearing\s+(?:a\s+)?|shirt\s*(?:is\s*)?|in\s+(?:a\s+)?)(\w+)\s*shirt",
            q,
        )
        if not shirt_match:
            # "wearing a red shirt" → "wearing a <color>"
            shirt_match = re.search(
                r"wearing\s+(?:a\s+)?(\w+)",
                q,
            )
        if shirt_match and shirt_match.group(1) in _COLORS:
            intent["shirt"] = shirt_match.group(1)
            if "object_type" not in intent:
                intent["object_type"] = "person"

        # pants color
        pants_match = re.search(r"(\w+)\s*(?:pants|trousers|jeans)", q)
        if pants_match and pants_match.group(1) in _COLORS:
            intent["pants"] = pants_match.group(1)
            if "object_type" not in intent:
                intent["object_type"] = "person"

    # ── Vehicle attributes ──
    if intent.get("object_type") == "vehicle" or is_vehicle:
        for vt in ["car", "truck", "motorcycle", "bus", "bike"]:
            if vt in q:
                intent["vehicle_type"] = vt
                break
        for c in _COLORS:
            if c in q:
                intent["vehicle_color"] = c
                break

    # ── Camera ID ──
    cam_match = _CAM_RE.search(query)
    if cam_match:
        cam_num = int(cam_match.group(1))
        intent["camera_id"] = f"CAM_{cam_num:02d}"

    # ── Camera Name / Location ──
    location_keywords = [
        ("front gate", "Front Gate"),
        ("gate", "Front Gate"),
        ("parking lot", "Parking Lot"),
        ("parking", "Parking Lot"),
        ("back door", "Back Door"),
        ("corridor", "Corridor"),
        ("room", "Room"),
    ]
    for loc_key, loc_name in location_keywords:
        if re.search(r"\b" + re.escape(loc_key) + r"\b", q):
            intent["camera_name"] = loc_name
            break

    # ── Time ──
    time_val = _parse_time(query)
    if time_val:
        if "before" in q:
            intent["time_before"] = time_val
        else:
            intent["time_after"] = time_val

    return intent

