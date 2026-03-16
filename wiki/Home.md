# Home

Welcome to the **MooAId** wiki!

**MooAId** (My Opinion AI Daemon) is an AI-powered opinion prediction system that analyzes your personality, preferences, values, and context to predict what your opinion would likely be on any given question.

> "Based on what I know about you, your likely opinion is..."

## Quick Links

- [[Installation Guide]]
- [[Profile Builder]]
- [[CLI Usage]]
- [[REST API Documentation]]
- [[Configuration]]
- [[Docker Deployment]]
- [[FAQ]]

## Features

- 🤖 **Multi AI Provider Support** - OpenRouter, Ollama (local), OpenAI, Google Gemini
- 📝 **User Profile System** - Store preferences, values, personality traits
- 🧠 **AI Profile Builder** - Interactive question-based profile creation with psychoanalysis
- 🔮 **Opinion Prediction Engine** - AI-powered opinion prediction based on your profile
- 🌐 **REST API** - Full-featured API for integration
- 💻 **CLI Tool** - Command-line interface for daily use
- 🎨 **Web UI** - Beautiful browser-based interface
- ⚙️ **Flexible Configuration** - YAML-based config system
- 🗄️ **SQLite Storage** - Persistent profile and history storage
- 🐳 **Docker Support** - Easy containerized deployment

## Getting Started

### 1. Install

```bash
git clone https://github.com/CertifiedSlop/MooAId.git
cd MooAId
pip install -e ".[dev]"
```

### 2. Configure

Edit `config.yaml` with your AI provider:

```yaml
provider: openrouter
openrouter:
  api_key: "sk-or-..."
  default_model: "anthropic/claude-3-haiku"
```

### 3. Build Your Profile

Use the AI-powered Profile Builder:

```bash
mooaid profile build default
```

### 4. Ask Questions

```bash
mooaid opinion ask "Should I learn Rust or Python?"
```

## Project Structure

```
MooAId/
├── mooaid/          # Main package
│   ├── api/         # FastAPI REST API
│   ├── cli/         # Typer CLI
│   ├── config/      # Configuration management
│   ├── core/        # Core logic (opinion engine, providers)
│   ├── profile/     # Profile management & builder
│   ├── providers/   # AI provider adapters
│   └── webui/       # Web interface
├── tests/           # Test suite
├── wiki/            # Documentation
└── docker-compose.yml
```

## Community

- **GitHub**: https://github.com/CertifiedSlop/MooAId
- **Issues**: https://github.com/CertifiedSlop/MooAId/issues
- **Discussions**: https://github.com/CertifiedSlop/MooAId/discussions

## License

MIT License - see [LICENSE](https://github.com/CertifiedSlop/MooAId/blob/main/LICENSE) for details.
