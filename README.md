# MooAId - My Opinion AI Daemon

**MooAId** stands for **"My Opinion AI Daemon"**.

Its purpose is simple: **If someone needs your opinion and you are not available, they can ask MooAId.**

MooAId analyzes your personality, preferences, values, and context to predict what your opinion would likely be on any given topic.

> "Based on what I know about you, your likely opinion is..."

This is **not a chatbot**. It is an **AI opinion predictor**.

---

## Features

- 🤖 **Multi AI Provider Support** - OpenRouter, Ollama (local), OpenAI, Google Gemini
- 📝 **User Profile System** - Store preferences, values, personality traits
- 🔮 **Opinion Prediction Engine** - AI-powered opinion prediction based on your profile
- 🌐 **REST API** - Full-featured API for integration
- 💻 **CLI Tool** - Command-line interface for daily use
- ⚙️ **Flexible Configuration** - YAML-based config system
- 🗄️ **SQLite Storage** - Persistent profile and history storage

---

## Installation

### Prerequisites

- Python 3.10 or higher
- pip or uv for package management

### Install from Source

```bash
# Clone the repository
git clone https://github.com/mooaid/mooaid.git
cd mooaid

# Install dependencies
pip install -e ".[dev]"

# Or using uv
uv pip install -e ".[dev]"
```

---

## Quick Start

### 1. Configure Your AI Provider

Edit `config.yaml` to set up your preferred AI provider:

```yaml
# For OpenRouter
provider: openrouter
openrouter:
  api_key: "your-api-key-here"
  default_model: "anthropic/claude-3-haiku"

# For Ollama (local, no API key needed)
provider: ollama
ollama:
  host: "http://localhost:11434"
  model: "llama3"

# For OpenAI
provider: openai
openai:
  api_key: "your-api-key-here"
  default_model: "gpt-3.5-turbo"

# For Google Gemini
provider: gemini
gemini:
  api_key: "your-api-key-here"
  default_model: "gemini-pro"
```

### 2. Create Your Profile

```bash
# Create a default profile
mooaid profile create default

# Add your preferences
mooaid profile add preferences "likes open source"
mooaid profile add preferences "prefers Linux"
mooaid profile add preferences "values performance over convenience"

# Add your values
mooaid profile add values "privacy"
mooaid profile add values "transparency"
mooaid profile add values "efficiency"

# Add personality traits
mooaid profile add personality "analytical"
mooaid profile add personality "pragmatic"
mooaid profile add personality "skeptical of hype"
```

### 3. Ask MooAId for an Opinion

```bash
# Using CLI
mooaid opinion ask "Should I learn Rust or Python?"

# Or use the REST API
curl -X POST http://localhost:8000/opinion \
  -H "Content-Type: application/json" \
  -d '{"question": "Should I learn Rust or Python?"}'
```

---

## Usage

### CLI Commands

#### Opinion Commands

```bash
# Ask a question
mooaid opinion ask "Is remote work better than office work?"

# Ask using a specific profile
mooaid opinion ask "What laptop should I buy?" --profile work
```

#### Profile Commands

```bash
# List all profiles
mooaid profile list

# Create a new profile
mooaid profile create myprofile

# Show profile details
mooaid profile show myprofile

# Add items to profile fields
mooaid profile add preferences "likes minimalism" --profile myprofile
mooaid profile add values "simplicity" --profile myprofile
mooaid profile add personality "detail-oriented" --profile myprofile
mooaid profile add context "works in tech industry" --profile myprofile

# Remove items from profile
mooaid profile remove preferences "likes minimalism" --profile myprofile

# Delete a profile
mooaid profile delete myprofile
```

#### Configuration Commands

```bash
# Show current configuration
mooaid config show

# Change provider
mooaid config provider ollama

# Change model
mooaid config model llama3 --provider ollama
```

#### Server Command

```bash
# Start the API server
mooaid serve

# Start with custom host/port
mooaid serve --host 0.0.0.0 --port 8080

# Enable auto-reload for development
mooaid serve --reload
```

---

### REST API

Start the server:

```bash
mooaid serve
```

API documentation is available at: `http://localhost:8000/docs`

#### Endpoints

##### `POST /opinion`

Predict an opinion for a question.

```bash
curl -X POST http://localhost:8000/opinion \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Should I buy a Mac or PC?",
    "profile_name": "default",
    "additional_context": ["currently a student", "budget is $1500"]
  }'
```

Response:

```json
{
  "predicted_opinion": "Based on what I know about you, your likely opinion is that a Mac would be the better choice...",
  "reasoning": "Your preference for quality hardware and Unix-based systems aligns with Mac...",
  "model": "llama3",
  "provider": "ollama",
  "profile_used": "default"
}
```

##### `GET /profile`

List all profiles.

```bash
curl http://localhost:8000/profile
```

##### `GET /profile/{name}`

Get a specific profile.

```bash
curl http://localhost:8000/profile/default
```

##### `POST /profile`

Create a new profile.

```bash
curl -X POST http://localhost:8000/profile \
  -H "Content-Type: application/json" \
  -d '{"name": "work"}'
```

##### `PUT /profile/{name}`

Update a profile's fields.

```bash
curl -X PUT http://localhost:8000/profile/default \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": ["likes open source", "prefers Linux"],
    "values": ["privacy", "transparency"]
  }'
```

##### `POST /profile/{name}/add`

Add items to a profile field.

```bash
curl -X POST http://localhost:8000/profile/default/add \
  -H "Content-Type: application/json" \
  -d '{
    "field": "preferences",
    "items": ["values performance"]
  }'
```

##### `DELETE /profile/{name}`

Delete a profile.

```bash
curl -X DELETE http://localhost:8000/profile/default
```

##### `GET /config`

Get current configuration.

```bash
curl http://localhost:8000/config
```

##### `GET /health`

Health check endpoint.

```bash
curl http://localhost:8000/health
```

---

## Architecture

```
mooaid/
├── core/                    # Core functionality
│   ├── __init__.py         # AIProvider interface
│   ├── provider_factory.py # Provider factory
│   └── opinion_engine.py   # Opinion prediction engine
├── providers/               # AI provider implementations
│   ├── __init__.py
│   ├── openrouter.py       # OpenRouter provider
│   ├── ollama.py           # Ollama (local) provider
│   ├── openai.py           # OpenAI provider
│   └── gemini.py           # Google Gemini provider
├── api/                     # REST API
│   └── __init__.py         # FastAPI application
├── cli/                     # Command-line interface
│   └── main.py             # Typer CLI
├── profile/                 # Profile management
│   ├── __init__.py         # Database & models
│   └── service.py          # Profile service
├── config/                  # Configuration
│   └── __init__.py         # Config management
├── utils/                   # Utilities
│   └── __init__.py         # Helper functions
└── __init__.py
```

---

## Configuration Reference

### config.yaml

```yaml
# Default AI provider (openrouter, ollama, openai, gemini)
provider: openrouter

# OpenRouter Configuration
openrouter:
  api_key: ""
  base_url: "https://openrouter.ai/api/v1"
  default_model: "anthropic/claude-3-haiku"

# Ollama Configuration
ollama:
  host: "http://localhost:11434"
  model: "llama3"

# OpenAI Configuration
openai:
  api_key: ""
  base_url: "https://api.openai.com/v1"
  default_model: "gpt-3.5-turbo"

# Google Gemini Configuration
gemini:
  api_key: ""
  default_model: "gemini-pro"

# Database Configuration
database:
  path: "./mooaid.db"

# API Configuration
api:
  host: "0.0.0.0"
  port: 8000

# Logging Configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## Profile Fields

MooAId stores four types of profile data:

| Field | Description | Example |
|-------|-------------|---------|
| `preferences` | Things you like/dislike | "likes open source", "prefers Linux" |
| `values` | Core values and principles | "privacy", "transparency", "efficiency" |
| `personality` | Personality traits | "analytical", "pragmatic", "skeptical" |
| `context` | Additional context about you | "works in tech", "budget-conscious" |

---

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black mooaid/
ruff check mooaid/
```

### Project Structure

The project uses a modular architecture designed for extensibility:

- **Provider Interface**: Easy to add new AI providers
- **Profile System**: Supports multi-user profiles
- **Opinion Engine**: Pluggable prompt templates
- **API/CLI**: Separate interfaces, shared core

---

## Future Extensions

Planned features:

- 🧠 **Vector Memory** - Store and retrieve opinion history with embeddings
- 🔍 **RAG Support** - Enhanced predictions using past opinions
- 📊 **UI Dashboard** - Web interface for profile management
- 👥 **Multi-User Profiles** - Support for multiple user profiles
- 📈 **Analytics** - Track opinion patterns over time
- 🔌 **Plugin System** - Extend with custom providers and features

---

## License

MIT License - See LICENSE file for details.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/mooaid/mooaid/issues
- Documentation: https://github.com/mooaid/mooaid/wiki
