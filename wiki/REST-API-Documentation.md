# REST API Documentation

Complete API reference for MooAId.

**Base URL:** `http://localhost:8000`

## Authentication

Currently, the API does not require authentication. For production use, consider adding authentication middleware.

## Endpoints

### Health

#### GET /health

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "provider_status": {
    "openrouter": true
  }
}
```

---

### Configuration

#### GET /config

Get current configuration.

**Response:**
```json
{
  "provider": "openrouter",
  "available_providers": ["openrouter", "ollama", "openai", "gemini"],
  "database_path": "./mooaid.db",
  "api_host": "0.0.0.0",
  "api_port": 8000,
  "openrouter_model": "anthropic/claude-3-haiku",
  "openai_model": "gpt-4o",
  "gemini_model": "gemini-pro",
  "ollama_model": "llama3"
}
```

#### PUT /config

Update configuration.

**Request:**
```json
{
  "provider": "openrouter",
  "openrouter_api_key": "sk-or-...",
  "openrouter_model": "anthropic/claude-3-sonnet"
}
```

**Response:** Same as GET /config

---

### Models

#### GET /models

Get available models for each provider.

**Response:**
```json
{
  "models": {
    "openrouter": [
      {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku"},
      {"id": "anthropic/claude-3-sonnet", "name": "Claude 3 Sonnet"}
    ],
    "openai": [
      {"id": "gpt-4o", "name": "GPT-4o"}
    ],
    "gemini": [
      {"id": "gemini-pro", "name": "Gemini Pro"}
    ],
    "ollama": [
      {"id": "llama3", "name": "Llama 3"}
    ]
  }
}
```

---

### Opinion

#### POST /opinion

Predict an opinion for a given question.

**Request:**
```json
{
  "question": "Should I learn Rust or Python?",
  "profile_name": "default",
  "additional_context": ["interested in systems programming"]
}
```

**Response:**
```json
{
  "predicted_opinion": "Based on what I know about you, your likely opinion is...",
  "reasoning": "This is based on your preferences for...",
  "model": "anthropic/claude-3-haiku",
  "provider": "openrouter",
  "profile_used": "default"
}
```

---

### Profile

#### GET /profile

List all profile names.

**Response:**
```json
["default", "work", "personal"]
```

#### GET /profile/{name}

Get a specific profile.

**Response:**
```json
{
  "name": "default",
  "preferences": ["likes open source", "prefers Linux"],
  "values": ["privacy", "transparency"],
  "personality": ["analytical", "pragmatic"],
  "context": ["works as software engineer"]
}
```

#### POST /profile

Create a new profile.

**Request:**
```json
{"name": "myprofile"}
```

**Response:** Same as GET /profile/{name}

#### PUT /profile/{name}

Update a profile's fields.

**Request:**
```json
{
  "preferences": ["new preference"],
  "values": ["new value"],
  "personality": ["new trait"],
  "context": ["new context"]
}
```

**Response:** Same as GET /profile/{name}

#### POST /profile/{name}/add

Add items to a profile field.

**Request:**
```json
{
  "field": "preferences",
  "items": ["new item 1", "new item 2"]
}
```

**Response:** Same as GET /profile/{name}

#### DELETE /profile/{name}

Delete a profile.

**Response:**
```json
{"message": "Profile 'myprofile' deleted successfully"}
```

---

### Profile Builder

#### POST /profile-builder/start

Start a new profile builder session.

**Request:**
```json
{"profile_name": "myprofile"}
```

**Response:**
```json
{
  "session_id": "abc123...",
  "profile_name": "myprofile"
}
```

#### POST /profile-builder/{session_id}/question

Get the next question.

**Response:**
```json
{
  "question": "What hobbies do you enjoy?",
  "category": "Interests & Hobbies",
  "question_number": 1,
  "total_questions": 11,
  "progress_percent": 0
}
```

#### POST /profile-builder/{session_id}/answer

Submit an answer.

**Request:**
```json
{"answer": "I love reading and hiking"}
```

**Response:**
```json
{
  "summary": "Person enjoys intellectual and outdoor activities",
  "extracted": {
    "preferences": ["reading", "hiking"],
    "values": [],
    "personality": [],
    "context": []
  },
  "progress": {
    "complete": false,
    "questions_answered": 1,
    "total_questions": 11,
    "progress_percent": 9
  }
}
```

#### POST /profile-builder/{session_id}/complete

Complete the session and save the profile.

**Response:**
```json
{
  "profile_name": "myprofile",
  "profile_data": {
    "preferences": ["reading", "hiking"],
    "values": ["curiosity"],
    "personality": ["analytical"],
    "context": ["works in tech"]
  },
  "summary": "Profile built with 2 preferences, 1 values, 1 personality traits, and 1 context items"
}
```

#### DELETE /profile-builder/{session_id}

Cancel a session.

**Response:**
```json
{"message": "Session cancelled"}
```

---

### History

#### GET /history

Get opinion history.

**Query Parameters:**
- `limit` (optional): Maximum items to return (default: 20)

**Response:**
```json
[
  {
    "id": 1,
    "profile_name": "default",
    "question": "Should I learn Rust or Python?",
    "predicted_opinion": "Based on what I know...",
    "reasoning": "This is based on...",
    "provider": "openrouter",
    "model": "anthropic/claude-3-haiku",
    "created_at": "2024-01-01T12:00:00Z"
  }
]
```

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid field. Must be one of: preferences, values, personality, context"
}
```

### 404 Not Found

```json
{
  "detail": "Profile 'myprofile' not found"
}
```

### 409 Conflict

```json
{
  "detail": "Profile 'default' already exists"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Prediction failed: OpenRouter API error: 401"
}
```

---

## Interactive Documentation

Visit the interactive API docs at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Rate Limiting

Currently, there is no rate limiting. For production use, consider adding rate limiting middleware.

## CORS

CORS is enabled for all origins by default. Configure in `mooaid/api/__init__.py` for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Next Steps

- [[Profile Builder]] - Interactive profile creation
- [[CLI Usage]] - Command-line interface
- [[Configuration]] - Configuration options
