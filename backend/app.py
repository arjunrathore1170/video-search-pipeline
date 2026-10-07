"""
Flask REST API – VisionQuery (Computer 2)
-------------------------------------------
Retrieval pipeline that:
  - Fetches events from Computer 1 over HTTP (GET /api/events)
  - Searches/filters events via natural language (POST /api/search)
  - Builds video retrieval URLs (uploaded video HTTP / NVR RTSP)
  - Proxies uploaded videos from Computer 1 for browser playback

Endpoints:
  GET  /                         – API info
  GET  /api/health               – Health check
  GET  /api/events               – Fetch + return events from Computer 1
  POST /api/search               – Natural-language search
  GET  /api/video-source/<id>    – Get video source info for an event
  GET  /api/nvr-config           – Get current NVR configuration (safe)
  GET  /proxy/video/<filename>   – Proxy uploaded video from Computer 1
"""

import json
import os
import requests as http_requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

from config import (
    get_computer_1_base_url,
    get_computer_1_events_url,
    get_computer_1_videos_url,
    set_computer_1_url,
    NVR_CREDENTIALS,
    NVR_TEMPLATES,
    DEFAULT_NVR_MANUFACTURER,
)
from video_retrieval import get_video_source

app = Flask(__name__)
CORS(app)

# Path to local events.json (fallback when Computer 1 is unreachable)
EVENTS_JSON_PATH = os.path.join(os.path.dirname(__file__), "events.json")


def _fetch_events():
    """Fetch events from Computer 1 over HTTP/HTTPS.

    Falls back to local events.json if Computer 1 is unreachable.
    """
    events_url = get_computer_1_events_url()
    try:
        resp = http_requests.get(events_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "events" in data:
            return data["events"], "computer_1"
        if isinstance(data, list):
            return data, "computer_1"
        return [], "computer_1"
    except Exception as e:
        print(f"[app] Computer 1 unreachable ({events_url}): {e}")
        print("[app] Using local events.json fallback")
        try:
            with open(EVENTS_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data, "local_fallback"
            return [], "local_fallback"
        except (FileNotFoundError, json.JSONDecodeError):
            return [], "local_fallback"


@app.route("/", methods=["GET"])
def home():
    """Root route returning API info."""
    c1_base = get_computer_1_base_url()
    return jsonify({
        "status": "online",
        "message": "VisionQuery – Computer 2 Retrieval Pipeline is running!",
        "computer_1": c1_base,
        "frontend_url": "http://localhost:5173",
        "endpoints": {
            "health": "GET /api/health",
            "events": "GET /api/events",
            "search": "POST /api/search",
            "video_source": "GET /api/video-source/<event_id>",
            "nvr_config": "GET /api/nvr-config",
            "computer_1_config": "GET/POST /api/config/computer-1",
            "proxy_video": "GET /proxy/video/<filename>",
        }
    })


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint with Computer 1 connectivity status."""
    c1_base = get_computer_1_base_url()
    comp1_status = "unknown"
    try:
        resp = http_requests.get(f"{c1_base}/api/events", timeout=3)
        comp1_status = "connected" if resp.ok else f"error ({resp.status_code})"
    except Exception:
        try:
            resp = http_requests.get(f"{c1_base}/", timeout=3)
            comp1_status = "connected" if resp.ok else f"error ({resp.status_code})"
        except Exception:
            comp1_status = "unreachable"

    return jsonify({
        "status": "ok",
        "computer_1": {
            "url": c1_base,
            "status": comp1_status,
        },
    })


@app.route("/api/config/computer-1", methods=["GET", "POST"])
def configure_computer_1():
    """Get or update Computer 1 connection settings at runtime.

    Allows connecting to Computer 1 across different cities/networks
    via public IP, Ngrok, Cloudflare Tunnel, or domain name.
    """
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        new_target = data.get("url") or data.get("ip") or ""
        port = data.get("port", 5000)

        if not new_target:
            return jsonify({"error": "Target URL or IP is required."}), 400

        updated_url = set_computer_1_url(new_target, port=int(port) if port else 5000)

        # Test reachability
        status = "unreachable"
        try:
            resp = http_requests.get(f"{updated_url}/api/events", timeout=4)
            if resp.ok:
                status = "connected"
            else:
                resp2 = http_requests.get(f"{updated_url}/", timeout=3)
                if resp2.ok:
                    status = "connected"
        except Exception:
            status = "unreachable"

        return jsonify({
            "message": "Computer 1 connection updated successfully.",
            "url": updated_url,
            "status": status,
        })

    # GET
    c1_base = get_computer_1_base_url()
    status = "unreachable"
    try:
        resp = http_requests.get(f"{c1_base}/api/events", timeout=3)
        if resp.ok:
            status = "connected"
    except Exception:
        status = "unreachable"

    return jsonify({
        "url": c1_base,
        "status": status,
    })


@app.route("/api/events", methods=["GET"])
def get_events():
    """Return all events, fetched from Computer 1.

    The frontend caches this response for 60 seconds and provides
    a Refresh button for on-demand re-fetch.
    """
    events, source = _fetch_events()

    # Enrich events with video source info
    enriched = []
    for event in events:
        enriched_event = dict(event)
        video_source = get_video_source(event)
        enriched_event["video_source"] = video_source
        enriched.append(enriched_event)

    return jsonify({
        "events": enriched,
        "count": len(enriched),
        "source": source,
    })


@app.route("/api/search", methods=["POST"])
def search():
    """Natural-language search endpoint.

    Request:  { "query": "..." }
    Response: { "query", "intent", "results", "used_fallback" }

    Falls back to keyword extraction when Ollama is unavailable.
    """
    from ollama_service import extract_intent
    from search_service import search_events

    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query cannot be empty."}), 400

    # Step 1 – Intent extraction
    try:
        intent, used_fallback = extract_intent(query)
    except Exception as e:
        return jsonify({
            "error": f"Intent extraction failed: {str(e)}",
        }), 500

    # Step 2 – Search events (fetches from Computer 1)
    try:
        results = search_events(intent)
    except Exception as e:
        return jsonify({
            "error": f"Database search failed: {str(e)}",
        }), 500

    # Step 3 – Build response
    return jsonify({
        "query": query,
        "intent": intent,
        "results": results,
        "result_count": len(results),
        "used_fallback": used_fallback,
    })


@app.route("/api/video-source/<int:event_id>", methods=["GET"])
def get_event_video_source(event_id):
    """Get video source info for a specific event by ID.

    Returns the video URL (HTTP or RTSP) and source type.
    """
    events, _ = _fetch_events()
    event = next((e for e in events if e.get("event_id") == event_id), None)

    if not event:
        return jsonify({"error": f"Event {event_id} not found."}), 404

    video_source = get_video_source(event)
    return jsonify({
        "event_id": event_id,
        "video_source": video_source,
    })


@app.route("/api/nvr-config", methods=["GET"])
def get_nvr_config():
    """Return the current NVR configuration (without passwords).

    Useful for the frontend settings panel.
    """
    safe_nvrs = {}
    for ip, cfg in NVR_CREDENTIALS.items():
        safe_nvrs[ip] = {
            "manufacturer": cfg.get("manufacturer", DEFAULT_NVR_MANUFACTURER),
            "username": cfg.get("username", ""),
            "has_password": bool(cfg.get("password")),
        }

    return jsonify({
        "nvrs": safe_nvrs,
        "templates": {k: {"url": v["url"], "time_format": v["time_format"]} for k, v in NVR_TEMPLATES.items()},
        "default_manufacturer": DEFAULT_NVR_MANUFACTURER,
    })


@app.route("/proxy/video/<path:filename>", methods=["GET"])
def proxy_video(filename):
    """Proxy an uploaded video from Computer 1 for browser playback.

    This allows the frontend to play uploaded videos without CORS issues.
    The video is streamed from Computer 1 in chunks to avoid loading
    the entire file into memory.
    """
    source_url = f"{get_computer_1_videos_url()}/{filename}"

    try:
        # Stream the video from Computer 1
        upstream = http_requests.get(source_url, stream=True, timeout=30)
        upstream.raise_for_status()

        # Determine content type
        content_type = upstream.headers.get("Content-Type", "video/mp4")
        content_length = upstream.headers.get("Content-Length")

        headers = {"Content-Type": content_type}
        if content_length:
            headers["Content-Length"] = content_length

        # Support Range requests for video seeking
        range_header = request.headers.get("Range")
        if range_header:
            # Re-request with Range header
            upstream.close()
            upstream = http_requests.get(
                source_url,
                stream=True,
                timeout=30,
                headers={"Range": range_header},
            )
            headers["Content-Range"] = upstream.headers.get("Content-Range", "")
            headers["Accept-Ranges"] = "bytes"
            if upstream.headers.get("Content-Length"):
                headers["Content-Length"] = upstream.headers.get("Content-Length")

            return Response(
                stream_with_context(upstream.iter_content(chunk_size=8192)),
                status=206,
                headers=headers,
            )

        headers["Accept-Ranges"] = "bytes"
        return Response(
            stream_with_context(upstream.iter_content(chunk_size=8192)),
            status=200,
            headers=headers,
        )

    except http_requests.exceptions.ConnectionError:
        return jsonify({
            "error": f"Could not connect to Computer 1 at {source_url}",
        }), 502
    except http_requests.exceptions.HTTPError as e:
        return jsonify({
            "error": f"Computer 1 returned error for {filename}: {e}",
        }), e.response.status_code if e.response else 502
    except Exception as e:
        return jsonify({
            "error": f"Failed to proxy video: {str(e)}",
        }), 500


if __name__ == "__main__":
    print("=" * 55)
    print("  VisionQuery – Computer 2 Retrieval Pipeline")
    print(f"  Backend:    http://localhost:5000")
    print(f"  Computer 1: {get_computer_1_base_url()}")
    print("=" * 55)
    app.run(debug=True, port=5000)
