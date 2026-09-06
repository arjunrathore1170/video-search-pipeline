"""
Mock Event Database
-------------------
Simulates the output of the offline video-processing pipeline.
Each event represents a detected object (person / vehicle) with
associated attributes and the camera timestamp range.

Replace this module with a real database adapter (SQLite / PostgreSQL)
when the offline pipeline is connected.
"""

EVENTS = [
    # ── Persons ──────────────────────────────────────────────
    {
        "camera_id": "CAM_01",
        "object_type": "person",
        "shirt": "red",
        "pants": "black",
        "start_time": "22:14:10",
        "end_time": "22:14:48",
    },
    {
        "camera_id": "CAM_01",
        "object_type": "person",
        "shirt": "red",
        "pants": "blue",
        "start_time": "22:51:32",
        "end_time": "22:52:15",
    },
    {
        "camera_id": "CAM_03",
        "object_type": "person",
        "shirt": "red",
        "pants": "black",
        "start_time": "23:20:01",
        "end_time": "23:20:41",
    },
    {
        "camera_id": "CAM_02",
        "object_type": "person",
        "shirt": "blue",
        "pants": "gray",
        "start_time": "09:15:00",
        "end_time": "09:15:42",
    },
    {
        "camera_id": "CAM_02",
        "object_type": "person",
        "shirt": "blue",
        "pants": "black",
        "start_time": "14:30:20",
        "end_time": "14:31:05",
    },
    {
        "camera_id": "CAM_01",
        "object_type": "person",
        "shirt": "white",
        "pants": "blue",
        "start_time": "08:05:10",
        "end_time": "08:05:55",
    },
    {
        "camera_id": "CAM_04",
        "object_type": "person",
        "shirt": "green",
        "pants": "black",
        "start_time": "19:45:30",
        "end_time": "19:46:12",
    },
    {
        "camera_id": "CAM_01",
        "object_type": "person",
        "shirt": "black",
        "pants": "gray",
        "start_time": "21:10:00",
        "end_time": "21:10:35",
    },
    {
        "camera_id": "CAM_03",
        "object_type": "person",
        "shirt": "yellow",
        "pants": "white",
        "start_time": "16:22:15",
        "end_time": "16:23:00",
    },
    {
        "camera_id": "CAM_02",
        "object_type": "person",
        "shirt": "red",
        "pants": "white",
        "start_time": "20:05:30",
        "end_time": "20:06:10",
    },
    {
        "camera_id": "CAM_04",
        "object_type": "person",
        "shirt": "blue",
        "pants": "blue",
        "start_time": "21:30:00",
        "end_time": "21:30:50",
    },
    {
        "camera_id": "CAM_01",
        "object_type": "person",
        "shirt": "gray",
        "pants": "black",
        "start_time": "23:55:10",
        "end_time": "23:55:48",
    },
    # ── Vehicles ─────────────────────────────────────────────
    {
        "camera_id": "CAM_01",
        "object_type": "vehicle",
        "vehicle_type": "car",
        "vehicle_color": "white",
        "start_time": "20:30:00",
        "end_time": "20:30:25",
    },
    {
        "camera_id": "CAM_02",
        "object_type": "vehicle",
        "vehicle_type": "car",
        "vehicle_color": "black",
        "start_time": "21:15:40",
        "end_time": "21:16:10",
    },
    {
        "camera_id": "CAM_03",
        "object_type": "vehicle",
        "vehicle_type": "motorcycle",
        "vehicle_color": "red",
        "start_time": "22:05:00",
        "end_time": "22:05:30",
    },
    {
        "camera_id": "CAM_01",
        "object_type": "vehicle",
        "vehicle_type": "truck",
        "vehicle_color": "blue",
        "start_time": "19:50:15",
        "end_time": "19:50:55",
    },
    {
        "camera_id": "CAM_04",
        "object_type": "vehicle",
        "vehicle_type": "car",
        "vehicle_color": "silver",
        "start_time": "23:10:00",
        "end_time": "23:10:40",
    },
    {
        "camera_id": "CAM_02",
        "object_type": "vehicle",
        "vehicle_type": "motorcycle",
        "vehicle_color": "black",
        "start_time": "08:45:30",
        "end_time": "08:46:00",
    },
    {
        "camera_id": "CAM_03",
        "object_type": "vehicle",
        "vehicle_type": "car",
        "vehicle_color": "white",
        "start_time": "15:20:10",
        "end_time": "15:20:50",
    },
    {
        "camera_id": "CAM_04",
        "object_type": "vehicle",
        "vehicle_type": "bus",
        "vehicle_color": "yellow",
        "start_time": "07:30:00",
        "end_time": "07:31:20",
    },
]


def get_events():
    """Return the full list of mock events.

    Replace this function body with a database query when
    migrating to a real persistence layer.
    """
    return EVENTS
