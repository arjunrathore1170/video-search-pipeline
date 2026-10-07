"""
VisionQuery — Video Retrieval Layer
------------------------------------
Determines the correct video source for a given event and builds
the appropriate URL or RTSP stream address.

Supports:
  1. Uploaded videos → HTTP retrieval from Computer 1
  2. NVR playback   → RTSP URL built per manufacturer:
     - Dahua
     - Hikvision
     - CP Plus
     - Custom

The event itself drives the source decision:
  - event["video_file"] is truthy  → uploaded video on Computer 1
  - event["nvr_ip"]     is truthy  → NVR playback
  - neither                        → unsupported/invalid event
"""

import os
from datetime import datetime

from config import (
    get_computer_1_videos_url,
    NVR_TEMPLATES,
    NVR_CREDENTIALS,
    DEFAULT_NVR_MANUFACTURER,
    DEFAULT_NVR_USERNAME,
    DEFAULT_NVR_PASSWORD,
)


# ── Public API ──────────────────────────────────────────────────


def get_video_source(event: dict) -> dict:
    """Determine video source and return retrieval information.

    Returns a dict with:
        source_type : "uploaded" | "nvr" | "unsupported"
        video_url   : HTTP URL for uploaded videos
        rtsp_url    : RTSP URL for NVR playback
        start_sec   : float, video-relative start offset (uploaded only)
        end_sec     : float, video-relative end offset (uploaded only)
        manufacturer: str, NVR manufacturer name (nvr only)
        error       : str or None

    The caller can use source_type to decide how to play/display the video.
    """
    video_file = event.get("video_file")
    nvr_ip = event.get("nvr_ip")

    if video_file:
        return _build_uploaded_source(event)
    elif nvr_ip:
        return _build_nvr_source(event)
    else:
        return {
            "source_type": "unsupported",
            "video_url": None,
            "rtsp_url": None,
            "error": "Event has no video_file and no nvr_ip — cannot determine video source.",
        }


# ── Uploaded Video ──────────────────────────────────────────────


def _build_uploaded_source(event: dict) -> dict:
    """Build an HTTP URL for an uploaded video on Computer 1.

    Computer 1 serves uploaded videos at:
        GET /videos/<filename>

    The event's video_file may be:
        "uploads/people-detection.mp4"   → extract basename
        "people-detection.mp4"           → use directly
    """
    raw_path = event["video_file"]

    # Extract just the filename (basename) — ignore any directory prefix
    filename = os.path.basename(raw_path)

    video_url = f"{get_computer_1_videos_url()}/{filename}"

    # Parse video-relative timestamps (HH:MM:SS format)
    start_sec = _parse_offset_to_seconds(event.get("start_time", ""))
    end_sec = _parse_offset_to_seconds(event.get("end_time", ""))

    return {
        "source_type": "uploaded",
        "video_url": video_url,
        "rtsp_url": None,
        "start_sec": start_sec,
        "end_sec": end_sec,
        "manufacturer": None,
        "error": None,
    }


def _parse_offset_to_seconds(time_str: str) -> float:
    """Convert a time offset string to total seconds.

    Handles:
        "00:00:29"         → 29.0   (HH:MM:SS video offset)
        "00:29"            → 29.0   (MM:SS)
        "2026-10-05 15:20:14" → returns None (not a relative offset)
    """
    if not time_str:
        return 0.0

    # If it looks like a full datetime, it's not a video-relative offset
    if len(time_str) > 8 and "-" in time_str:
        return 0.0

    parts = time_str.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        else:
            return float(time_str)
    except (ValueError, TypeError):
        return 0.0


# ── NVR Playback ────────────────────────────────────────────────


def _build_nvr_source(event: dict) -> dict:
    """Build an RTSP playback URL for an NVR event.

    Combines:
        - NVR credentials from config (looked up by nvr_ip)
        - NVR manufacturer URL template
        - Event's nvr_ip, nvr_channel, start_time, end_time
    """
    nvr_ip = event["nvr_ip"]
    nvr_channel = event.get("nvr_channel", 1)
    start_time = event.get("start_time", "")
    end_time = event.get("end_time", "")

    # Look up NVR credentials
    nvr_config = NVR_CREDENTIALS.get(nvr_ip, {})
    manufacturer = nvr_config.get("manufacturer", DEFAULT_NVR_MANUFACTURER).lower()
    username = nvr_config.get("username", DEFAULT_NVR_USERNAME)
    password = nvr_config.get("password", DEFAULT_NVR_PASSWORD)

    # Get URL template for manufacturer
    template_config = NVR_TEMPLATES.get(manufacturer)
    if not template_config:
        return {
            "source_type": "nvr",
            "video_url": None,
            "rtsp_url": None,
            "manufacturer": manufacturer,
            "error": f"Unknown NVR manufacturer: {manufacturer}",
        }

    # Allow per-NVR URL/format overrides (especially useful for "custom")
    url_template = nvr_config.get("url_override", template_config["url"])
    time_format = nvr_config.get("time_format_override", template_config["time_format"])

    if not url_template:
        return {
            "source_type": "nvr",
            "video_url": None,
            "rtsp_url": None,
            "manufacturer": manufacturer,
            "error": f"No URL template configured for manufacturer '{manufacturer}'. "
                     f"Please configure it in config.py NVR_TEMPLATES or per-NVR url_override.",
        }

    # Convert timestamps to manufacturer-specific format
    start_formatted = _format_nvr_timestamp(start_time, time_format)
    end_formatted = _format_nvr_timestamp(end_time, time_format)

    if start_formatted is None or end_formatted is None:
        return {
            "source_type": "nvr",
            "video_url": None,
            "rtsp_url": None,
            "manufacturer": manufacturer,
            "error": f"Could not parse timestamps: start='{start_time}', end='{end_time}'",
        }

    # Build the RTSP URL by substituting placeholders
    try:
        rtsp_url = url_template.format(
            username=username,
            password=password,
            ip=nvr_ip,
            channel=nvr_channel,
            start=start_formatted,
            end=end_formatted,
            # Hikvision uses {starttime}/{endtime} in some templates
            starttime=start_formatted,
            endtime=end_formatted,
        )
    except KeyError as e:
        return {
            "source_type": "nvr",
            "video_url": None,
            "rtsp_url": None,
            "manufacturer": manufacturer,
            "error": f"URL template has unknown placeholder: {e}",
        }

    return {
        "source_type": "nvr",
        "video_url": None,
        "rtsp_url": rtsp_url,
        "manufacturer": manufacturer,
        "error": None,
    }


def _format_nvr_timestamp(dt_str: str, fmt: str) -> str | None:
    """Convert a datetime string to the manufacturer's timestamp format.

    Input formats supported:
        "2026-10-05 15:20:14"   → full datetime
        "2026-10-05T15:20:14"   → ISO variant

    The output is formatted using the manufacturer's strftime format.
    """
    if not dt_str or not fmt:
        return None

    # Try common datetime input formats
    for input_fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
        try:
            dt = datetime.strptime(dt_str, input_fmt)
            return dt.strftime(fmt)
        except ValueError:
            continue

    return None


# ── Utility ─────────────────────────────────────────────────────


def is_uploaded_video_event(event: dict) -> bool:
    """Check whether an event refers to an uploaded video."""
    return bool(event.get("video_file"))


def is_nvr_event(event: dict) -> bool:
    """Check whether an event refers to an NVR/IP camera."""
    return bool(event.get("nvr_ip"))


def get_nvr_manufacturer(event: dict) -> str | None:
    """Return the configured manufacturer for an NVR event."""
    nvr_ip = event.get("nvr_ip")
    if not nvr_ip:
        return None
    nvr_config = NVR_CREDENTIALS.get(nvr_ip, {})
    return nvr_config.get("manufacturer", DEFAULT_NVR_MANUFACTURER)
