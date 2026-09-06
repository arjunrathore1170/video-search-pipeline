"""
Flask REST API – Video Search Pipeline
---------------------------------------
Reads events.json (produced by YOLO + tracking pipeline) and exposes:
  GET  /api/events   – returns the latest events from events.json
  POST /api/search   – natural-language search (legacy, kept for compat)
  GET  /api/health   – health check

No Redis caching on the backend — caching is handled on the frontend side.
"""

import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Path to events.json (written by the CV pipeline)
EVENTS_JSON_PATH = os.path.join(os.path.dirname(__file__), "events.json")


def _load_events():
    """Read and return the latest events from events.json.

    Returns an empty list if the file does not exist or is invalid.
    """
    try:
        with open(EVENTS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


@app.route("/", methods=["GET"])
def home():
    """Root route returning API info."""
    return jsonify({
        "status": "online",
        "message": "Video Search Pipeline Flask REST API is running successfully!",
        "frontend_url": "http://localhost:5173",
        "endpoints": {
            "health": "GET /api/health",
            "events": "GET /api/events",
            "search": "POST /api/search"
        }
    })


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


@app.route("/api/events", methods=["GET"])
def get_events():
    """Return all events from events.json.

    The frontend caches this response for 60 seconds and provides
    a Refresh button for on-demand re-fetch.
    """
    events = _load_events()
    return jsonify({
        "events": events,
        "count": len(events),
    })


@app.route("/api/search", methods=["POST"])
def search():
    """Natural-language search endpoint (legacy compatibility).

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

    # Step 2 – Search events (now reads from events.json too)
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


if __name__ == "__main__":
    print("=" * 50)
    print("  Video Search Pipeline – Flask Backend")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
