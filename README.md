# Video Search Pipeline – Online Search Module

AI-powered natural language video search system. Ask questions about recorded camera footage and get relevant video timestamps.

## Architecture

```
User Natural Language Query
        ↓
  Llama 3 / Ollama
        ↓
  Structured Intent (JSON)
        ↓
  Event Database Search
        ↓
  Matching Video Timestamps
        ↓
  Frontend Display
```

## Project Structure

```
video-search-pipeline/
├── frontend/           # Vue.js 3 + Vite
│   └── src/
│       ├── components/
│       │   ├── ChatWindow.vue
│       │   ├── ChatMessage.vue
│       │   ├── SearchInput.vue
│       │   ├── IntentCard.vue
│       │   ├── VideoResultCard.vue
│       │   └── PipelineIndicator.vue
│       ├── App.vue
│       ├── main.js
│       └── style.css
│
└── backend/            # Flask REST API
    ├── app.py
    ├── ollama_service.py
    ├── search_service.py
    ├── mock_database.py
    └── requirements.txt
```

## Quick Start

### 1. Backend (Flask)

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

The API will be running at **http://localhost:5000**.

### 2. Frontend (Vue.js)

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The UI will be available at **http://localhost:5173**.

### 3. Ollama + Llama 3 (Optional)

If you have Ollama installed:

```bash
# Pull the Llama 3 model
ollama pull llama3

# Ollama runs automatically on http://localhost:11434
```

If Ollama is **not installed**, the system automatically falls back to a keyword-based intent extractor. The demo works fully without Ollama.

## API

### `POST /api/search`

**Request:**
```json
{
  "query": "Show the person wearing a red shirt after 10 PM"
}
```

**Response:**
```json
{
  "query": "Show the person wearing a red shirt after 10 PM",
  "intent": {
    "object_type": "person",
    "shirt": "red",
    "time_after": "22:00"
  },
  "results": [
    {
      "camera_id": "CAM_01",
      "start_time": "22:14:10",
      "end_time": "22:14:48",
      "duration": "38 sec"
    }
  ],
  "result_count": 1,
  "used_fallback": false
}
```

### `GET /api/health`

Returns `{ "status": "ok" }`.

## Example Queries

| Query | Extracted Intent |
|---|---|
| Show the person wearing a red shirt after 10 PM | `{ "object_type": "person", "shirt": "red", "time_after": "22:00" }` |
| Find a person wearing a blue shirt | `{ "object_type": "person", "shirt": "blue" }` |
| Show vehicles after 8 PM | `{ "object_type": "vehicle", "time_after": "20:00" }` |
| Find a person in camera 1 after 9 PM | `{ "object_type": "person", "camera_id": "CAM_01", "time_after": "21:00" }` |

## Technology Stack

- **Frontend:** Vue.js 3, Vite, Plain CSS
- **Backend:** Python, Flask, Flask-CORS
- **LLM:** Ollama + Llama 3 (with keyword fallback)
- **Database:** Mock JSON (replaceable with SQLite/PostgreSQL)
