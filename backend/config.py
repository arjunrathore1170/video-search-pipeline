"""
VisionQuery — Central Configuration
------------------------------------
All configurable settings for the Computer 2 retrieval pipeline.

Stores:
  - Computer 1 connection (IP, port)
  - NVR credentials and manufacturer settings
  - URL templates and timestamp formats per manufacturer

SECURITY: NVR credentials are stored here, NOT in events.json.
"""

import json
import os
import re

# ── Dynamic Settings Persistence ────────────────────────────────
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")


def _load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[config] Could not read {SETTINGS_FILE}: {e}")
    return {}


def _save_settings(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[config] Could not save {SETTINGS_FILE}: {e}")


_saved_settings = _load_settings()

# ── Computer 1 (Offline Pipeline Server) ────────────────────────
# Supports:
#   - Public domain or tunnel (e.g. "https://abc.ngrok-free.app", "https://c1.mycctv.com")
#   - Public IP or VPN (e.g. "http://203.0.113.19:5000", "http://100.64.1.2:5000")
#   - Local LAN (e.g. "192.168.0.155", "http://192.168.0.155:5000")

def normalize_computer_1_url(target: str, default_port: int = 5000) -> str:
    """Normalize user input (IP, hostname, or full URL) into a standard base URL."""
    target = (target or "").strip().rstrip("/")
    if not target:
        target = "192.168.0.155"

    if target.startswith("http://") or target.startswith("https://"):
        return target

    # If it contains a port like "1.2.3.4:5000" or "mydomain.com:5000"
    if ":" in target and not target.endswith("]"):
        return f"http://{target}"

    # Plain IP or domain: append default port
    return f"http://{target}:{default_port}"


_initial_c1 = _saved_settings.get("computer_1_url") or os.environ.get("COMPUTER_1_URL")
if not _initial_c1:
    _env_ip = os.environ.get("COMPUTER_1_IP", "192.168.0.155")
    _env_port = int(os.environ.get("COMPUTER_1_PORT", "5000"))
    _initial_c1 = f"http://{_env_ip}:{_env_port}"

COMPUTER_1_BASE_URL = normalize_computer_1_url(_initial_c1)
COMPUTER_1_EVENTS_URL = f"{COMPUTER_1_BASE_URL}/api/events"
COMPUTER_1_VIDEOS_URL = f"{COMPUTER_1_BASE_URL}/videos"

# For backwards compatibility with code expecting IP / Port
COMPUTER_1_IP = "192.168.0.155"
COMPUTER_1_PORT = 5000


def get_computer_1_base_url() -> str:
    global COMPUTER_1_BASE_URL
    return COMPUTER_1_BASE_URL


def get_computer_1_events_url() -> str:
    return f"{get_computer_1_base_url()}/api/events"


def get_computer_1_videos_url() -> str:
    return f"{get_computer_1_base_url()}/videos"


def set_computer_1_url(target: str, port: int = 5000) -> str:
    """Dynamically update Computer 1's URL at runtime and persist it."""
    global COMPUTER_1_BASE_URL, COMPUTER_1_EVENTS_URL, COMPUTER_1_VIDEOS_URL, COMPUTER_1_IP, COMPUTER_1_PORT
    new_url = normalize_computer_1_url(target, default_port=port)
    COMPUTER_1_BASE_URL = new_url
    COMPUTER_1_EVENTS_URL = f"{new_url}/api/events"
    COMPUTER_1_VIDEOS_URL = f"{new_url}/videos"

    # Update IP/Port if extractable
    m = re.search(r"://([^:/]+)(?::(\d+))?", new_url)
    if m:
        COMPUTER_1_IP = m.group(1)
        if m.group(2):
            COMPUTER_1_PORT = int(m.group(2))

    # Persist
    settings = _load_settings()
    settings["computer_1_url"] = new_url
    _save_settings(settings)

    print(f"[config] Computer 1 URL updated to: {new_url}")
    return new_url


# ── NVR Manufacturer URL Templates ──────────────────────────────
#
# Each manufacturer entry contains:
#   url          — RTSP playback URL template with placeholders:
#                    {username}, {password}, {ip}, {channel}, {start}, {end}
#   time_format  — strftime format string for converting datetime → URL timestamp
#
# These are configurable per manufacturer because exact URL syntax
# varies by model and firmware version.

NVR_TEMPLATES = {
    "dahua": {
        "url": "rtsp://{username}:{password}@{ip}:554/cam/playback?channel={channel}&starttime={start}&endtime={end}",
        "time_format": "%Y_%m_%d_%H_%M_%S",
    },
    "hikvision": {
        "url": "rtsp://{username}:{password}@{ip}:554/Streaming/tracks/{channel}01?starttime={start}&endtime={end}",
        "time_format": "%Y%m%dt%H%M%Sz",
    },
    "cp_plus": {
        "url": "rtsp://{username}:{password}@{ip}:554/cam/playback?channel={channel}&starttime={start}&endtime={end}",
        "time_format": "%Y_%m_%d_%H_%M_%S",
    },
    "custom": {
        "url": "",
        "time_format": "",
    },
}


# ── NVR Credentials ─────────────────────────────────────────────
#
# Maps NVR IP → credentials + manufacturer.
# Events only contain nvr_ip and nvr_channel — credentials are looked up here.
#
# Example (update with your actual NVR details):
#
#   "192.168.0.112": {
#       "manufacturer": "dahua",
#       "username": "admin",
#       "password": "your_password_here",
#   }
#
# For custom NVR, you can also override the URL template per-NVR:
#
#   "192.168.0.200": {
#       "manufacturer": "custom",
#       "username": "admin",
#       "password": "pass",
#       "url_override": "rtsp://{username}:{password}@{ip}:554/custom/playback?ch={channel}&from={start}&to={end}",
#       "time_format_override": "%Y_%m_%d_%H_%M_%S",
#   }

NVR_CREDENTIALS = {
    # ── Example Dahua NVR ──
    "192.168.0.112": {
        "manufacturer": "dahua",
        "username": "admin",
        "password": "admin123",
    },
    # ── Example Hikvision NVR ──
    # "192.168.0.113": {
    #     "manufacturer": "hikvision",
    #     "username": "admin",
    #     "password": "hik_password",
    # },
    # ── Example CP Plus NVR ──
    # "192.168.0.114": {
    #     "manufacturer": "cp_plus",
    #     "username": "admin",
    #     "password": "cp_password",
    # },
    # ── Example Custom NVR ──
    # "192.168.0.200": {
    #     "manufacturer": "custom",
    #     "username": "admin",
    #     "password": "custom_pass",
    #     "url_override": "rtsp://{username}:{password}@{ip}:554/custom/playback?ch={channel}&from={start}&to={end}",
    #     "time_format_override": "%Y_%m_%d_%H_%M_%S",
    # },
}


# ── Default NVR Manufacturer ────────────────────────────────────
# Used when an NVR IP is not found in NVR_CREDENTIALS.
# Set to "dahua", "hikvision", "cp_plus", or "custom".
DEFAULT_NVR_MANUFACTURER = os.environ.get("DEFAULT_NVR_MANUFACTURER", "dahua")

# Default NVR credentials (fallback when IP not in NVR_CREDENTIALS)
DEFAULT_NVR_USERNAME = os.environ.get("DEFAULT_NVR_USERNAME", "admin")
DEFAULT_NVR_PASSWORD = os.environ.get("DEFAULT_NVR_PASSWORD", "admin123")
