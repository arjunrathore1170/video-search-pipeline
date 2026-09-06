"""
Search Service
--------------
Filters events from events.json based on the structured intent
extracted from the user's natural-language query.

Updated to work with the new schema:
  { event_id, track_id, object_type, start_time, end_time, attributes: { shirt, pants }, video_file }
"""

import json
import os
from datetime import datetime

EVENTS_JSON_PATH = os.path.join(os.path.dirname(__file__), "events.json")


def _load_events():
    """Read events from events.json."""
    try:
        with open(EVENTS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _parse_datetime(dt_str: str) -> datetime | None:
    """Parse a datetime string in format 'YYYY-MM-DD HH:MM:SS'."""
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def _duration_label(start_str: str, end_str: str) -> str:
    """Human-readable duration between two timestamps."""
    start = _parse_datetime(start_str)
    end = _parse_datetime(end_str)
    if start and end:
        diff = int((end - start).total_seconds())
        if diff < 0:
            diff += 86400
        return f"{diff} sec"
    return "?"


def search_events(intent: dict) -> list[dict]:
    """Filter events that match every non-null intent field.

    Supported intent fields (mapped to new schema):
        object_type, shirt (→ attributes.shirt), pants (→ attributes.pants),
        time_after, time_before, event_id, track_id
    """
    events = _load_events()
    results = []

    for event in events:
        match = True
        attrs = event.get("attributes", {})

        # ── Exact-match fields ──
        if intent.get("object_type"):
            if event.get("object_type", "").lower() != intent["object_type"].lower():
                match = False

        if match and intent.get("shirt"):
            if attrs.get("shirt", "").lower() != intent["shirt"].lower():
                match = False

        if match and intent.get("pants"):
            if attrs.get("pants", "").lower() != intent["pants"].lower():
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

        if not match:
            continue

        # ── Time range filters ──
        event_start = _parse_datetime(event.get("start_time", ""))

        if event_start and intent.get("time_after"):
            # time_after can be HH:MM (compare time part only) or full datetime
            threshold = intent["time_after"]
            if ":" in threshold and len(threshold) <= 5:
                # HH:MM format — compare time-of-day
                parts = threshold.split(":")
                threshold_hour = int(parts[0])
                threshold_min = int(parts[1]) if len(parts) > 1 else 0
                if (event_start.hour * 60 + event_start.minute) < (threshold_hour * 60 + threshold_min):
                    match = False
            else:
                threshold_dt = _parse_datetime(threshold)
                if threshold_dt and event_start < threshold_dt:
                    match = False

        if event_start and intent.get("time_before"):
            threshold = intent["time_before"]
            if ":" in threshold and len(threshold) <= 5:
                parts = threshold.split(":")
                threshold_hour = int(parts[0])
                threshold_min = int(parts[1]) if len(parts) > 1 else 0
                if (event_start.hour * 60 + event_start.minute) > (threshold_hour * 60 + threshold_min):
                    match = False
            else:
                threshold_dt = _parse_datetime(threshold)
                if threshold_dt and event_start > threshold_dt:
                    match = False

        if match:
            result = {
                "event_id": event.get("event_id"),
                "track_id": event.get("track_id"),
                "object_type": event.get("object_type", ""),
                "start_time": event.get("start_time", ""),
                "end_time": event.get("end_time", ""),
                "duration": _duration_label(event.get("start_time", ""), event.get("end_time", "")),
                "attributes": attrs,
                "video_file": event.get("video_file"),
                "start_sec": event.get("start_sec"),
                "end_sec": event.get("end_sec"),
            }
            results.append(result)

    # Sort by start time
    results.sort(key=lambda r: r["start_time"])

    return results
