"""
Search Service
--------------
Filters events based on the structured intent extracted from the
user's natural-language query.

Updated to:
  - Fetch events from Computer 1 over HTTP (GET /api/events)
  - Support new schema fields: camera_id, camera_name, nvr_ip, nvr_channel
  - Handle nested attributes (attributes.shirt, attributes.pants)
  - Handle both datetime timestamps (NVR) and time-offset timestamps (uploaded)
  - Enrich results with video source info (uploaded URL / NVR RTSP URL)
"""

import json
import os
import re
import requests
from datetime import datetime

from config import get_computer_1_events_url
from video_retrieval import get_video_source


# ── Fallback: local events.json (used when Computer 1 is unreachable) ──

EVENTS_JSON_PATH = os.path.join(os.path.dirname(__file__), "events.json")


def _fetch_events_from_computer_1() -> list:
    """Fetch events from Computer 1 over HTTP/HTTPS.

    Endpoint: GET /api/events
    Falls back to local events.json if Computer 1 is unreachable.
    """
    events_url = get_computer_1_events_url()
    try:
        resp = requests.get(events_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        # Computer 1 returns { "events": [...], "count": N }
        if isinstance(data, dict) and "events" in data:
            return data["events"]
        # Direct array response
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"[search_service] Could not reach Computer 1 ({events_url}): {e}")
        print("[search_service] Falling back to local events.json")
        return _load_local_events()


def _load_local_events() -> list:
    """Read events from local events.json (fallback)."""
    try:
        with open(EVENTS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# ── Timestamp Parsing ───────────────────────────────────────────


def _parse_datetime(dt_str: str) -> datetime | None:
    """Parse a datetime string in format 'YYYY-MM-DD HH:MM:SS'."""
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def _is_relative_timestamp(dt_str: str) -> bool:
    """Check if a timestamp is a video-relative offset (HH:MM:SS) vs a real datetime.

    Relative:  "00:00:29", "01:23:45"
    Absolute:  "2026-10-05 15:20:14"
    """
    if not dt_str:
        return False
    return len(dt_str) <= 8 and ":" in dt_str and "-" not in dt_str


def _parse_time_to_minutes(time_str: str) -> int | None:
    """Parse HH:MM or HH:MM:SS to total minutes for time-of-day comparison."""
    parts = time_str.split(":")
    try:
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        return h * 60 + m
    except (ValueError, IndexError):
        return None


def _duration_label(start_str: str, end_str: str) -> str:
    """Human-readable duration between two timestamps."""
    # Try full datetime first
    start = _parse_datetime(start_str)
    end = _parse_datetime(end_str)
    if start and end:
        diff = int((end - start).total_seconds())
        if diff < 0:
            diff += 86400
        return f"{diff} sec"

    # Try relative time (HH:MM:SS)
    if _is_relative_timestamp(start_str) and _is_relative_timestamp(end_str):
        try:
            s_parts = start_str.split(":")
            e_parts = end_str.split(":")
            s_sec = int(s_parts[0]) * 3600 + int(s_parts[1]) * 60 + int(s_parts[2]) if len(s_parts) == 3 else 0
            e_sec = int(e_parts[0]) * 3600 + int(e_parts[1]) * 60 + int(e_parts[2]) if len(e_parts) == 3 else 0
            diff = e_sec - s_sec
            return f"{diff} sec" if diff >= 0 else "?"
        except (ValueError, IndexError):
            pass

    return "?"


# ── Search / Filter ─────────────────────────────────────────────


def search_events(intent: dict) -> list[dict]:
    """Filter events that match every non-null intent field.

    Supported intent fields (mapped to new schema):
        object_type          → event.object_type
        shirt                → event.attributes.shirt
        pants                → event.attributes.pants
        camera_name          → event.camera_name (fuzzy/substring match)
        camera_id            → event.camera_id
        time_after           → event.start_time >= threshold
        time_before          → event.start_time <= threshold
        event_id             → event.event_id
        track_id             → event.track_id
        vehicle_type         → event.object_type (legacy compat)
        vehicle_color        → event.attributes (legacy compat)
    """
    events = _fetch_events_from_computer_1()
    results = []

    for event in events:
        match = True
        attrs = event.get("attributes", {})

        # ── Exact-match fields ──

        # ── Object type matching ──
        if intent.get("object_type"):
            query_type = intent["object_type"].lower()
            event_type = event.get("object_type", "").lower()
            vehicle_classes = {"vehicle", "car", "truck", "motorcycle", "bus", "bike", "van"}

            if query_type == "vehicle" and event_type in vehicle_classes:
                pass  # match!
            elif event_type != query_type:
                match = False

        # ── Attributes (shirt / pants) ──
        def _normalize_color(c: str) -> str:
            c = c.lower().strip()
            return "gray" if c == "grey" else c

        if match and intent.get("shirt"):
            if _normalize_color(attrs.get("shirt", "")) != _normalize_color(intent["shirt"]):
                match = False

        if match and intent.get("pants"):
            if _normalize_color(attrs.get("pants", "")) != _normalize_color(intent["pants"]):
                match = False

        if match and intent.get("event_id"):
            try:
                if event.get("event_id") != int(intent["event_id"]):
                    match = False
            except (ValueError, TypeError):
                match = False

        if match and intent.get("track_id"):
            try:
                if event.get("track_id") != int(intent["track_id"]):
                    match = False
            except (ValueError, TypeError):
                match = False

        # ── Camera name (fuzzy/substring match) ──
        if match and intent.get("camera_name"):
            event_cam_name = (event.get("camera_name") or "").lower()
            query_cam_name = intent["camera_name"].lower()
            if query_cam_name not in event_cam_name:
                match = False

        # ── Camera ID (exact or numeric match) ──
        if match and intent.get("camera_id"):
            event_cam_id = event.get("camera_id")
            intent_cam_id = intent["camera_id"]
            # Handle both string "CAM_01" and numeric 1 formats
            if isinstance(event_cam_id, int) and isinstance(intent_cam_id, str):
                # Extract number from "CAM_01" format
                cam_num = re.search(r"(\d+)", str(intent_cam_id))
                if cam_num:
                    if event_cam_id != int(cam_num.group(1)):
                        match = False
                else:
                    match = False
            elif str(event_cam_id) != str(intent_cam_id):
                match = False

        if not match:
            continue

        # ── Time range filters ──
        event_start_str = event.get("start_time", "")

        # Skip time filtering for relative timestamps (uploaded video offsets)
        if not _is_relative_timestamp(event_start_str):
            event_start = _parse_datetime(event_start_str)

            if event_start and intent.get("time_after"):
                threshold = intent["time_after"]
                if ":" in threshold and len(threshold) <= 5:
                    # HH:MM format — compare time-of-day only
                    threshold_min = _parse_time_to_minutes(threshold)
                    event_min = event_start.hour * 60 + event_start.minute
                    if threshold_min is not None and event_min < threshold_min:
                        match = False
                else:
                    threshold_dt = _parse_datetime(threshold)
                    if threshold_dt and event_start < threshold_dt:
                        match = False

            if event_start and intent.get("time_before"):
                threshold = intent["time_before"]
                if ":" in threshold and len(threshold) <= 5:
                    threshold_min = _parse_time_to_minutes(threshold)
                    event_min = event_start.hour * 60 + event_start.minute
                    if threshold_min is not None and event_min > threshold_min:
                        match = False
                else:
                    threshold_dt = _parse_datetime(threshold)
                    if threshold_dt and event_start > threshold_dt:
                        match = False

        if match:
            # Build video source info
            video_source = get_video_source(event)

            result = {
                "event_id": event.get("event_id"),
                "track_id": event.get("track_id"),
                "camera_id": event.get("camera_id"),
                "camera_name": event.get("camera_name"),
                "object_type": event.get("object_type", ""),
                "start_time": event.get("start_time", ""),
                "end_time": event.get("end_time", ""),
                "duration": _duration_label(
                    event.get("start_time", ""), event.get("end_time", "")
                ),
                "attributes": attrs,
                "video_file": event.get("video_file"),
                "nvr_ip": event.get("nvr_ip"),
                "nvr_channel": event.get("nvr_channel"),
                # Video retrieval info
                "video_source": video_source,
            }
            results.append(result)

    # Sort by start time (full datetimes first, then offsets)
    results.sort(key=lambda r: r["start_time"])

    return results
