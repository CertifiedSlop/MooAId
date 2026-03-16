# Configuration

How to configure MooAId for your needs.

## Configuration File

The main configuration file is `config.yaml` in the project root.

### Default Configuration

```yaml
# AI Provider (openrouter, ollama, openai, gemini)
provider: openrouter

# OpenRouter Settings
openrouter:
  api_key: ""
  default_model: "anthropic/claude-3-haiku"

# Ollama Settings
ollama:
  host: "http://localhost:11434"
  model: "llama3"

# OpenAI Settings
openai:
  api_key: ""
  default_model: "gpt-4o"

# Gemini Settings
gemini:
  api_key: ""
  default_model: "gemini-pro"

# Database Settings
database:
  path: "./mooaid.db"

# API Settings
api:
  host: "0.0.0.0"
  port: 8000

# Logging Settings
logging:
  level: "INFO"
```

---

## AI Providers

### OpenRouter (Recommended)

OpenRouter provides access to multiple AI models through a single API.

**Setup:**
1. Get API key from https://openrouter.ai
2. Update config:

```yaml
provider: openrouter
openrouter:
  api_key: "sk-or-..."
  default_model: "anthropic/claude-3-haiku"
```

**Available Models:**
- `anthropic/claude-3-haiku` - Fast, affordable
- `anthropic/claude-3-sonnet` - Balanced
- `anthropic/claude-3-opus` - Most capable
- `openai/gpt-4o` - OpenAI's latest
- `meta-llama/llama-3-70b-instruct` - Open source

### Ollama (Local, Free)

Run AI models locally without API keys.

**Setup:**
1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull llama3`
3. Update config:

```yaml
provider: ollama
ollama:
  host: "http://localhost:11434"
  model: "llama3"
```

**Available Models:**
- `llama3` - Meta's Llama 3
- `llama2` - Meta's Llama 2
- `mistral` - Mistral AI
- `gemma` - Google's Gemma

### OpenAI

Direct integration with OpenAI's API.

**Setup:**
1. Get API key from https://platform.openai.com
2. Update config:

```yaml
provider: openai
openai:
  api_key: "sk-..."
  default_model: "gpt-4o"
```

**Available Models:**
- `gpt-4o` - Latest and greatest
- `gpt-4-turbo` - GPT-4 Turbo
- `gpt-3.5-turbo` - Fast and cheap

### Google Gemini

Google's AI models.

**Setup:**
1. Get API key from https://makersuite.google.com
2. Update config:

```yaml
provider: gemini
gemini:
  api_key: "AIza..."
  default_model: "gemini-pro"
```

**Available Models:**
- `gemini-pro` - Standard model
- `gemini-1.5-pro` - Latest model

---

## Environment Variables

Override config file settings with environment variables:

```bash
# Provider
export MOOAID_PROVIDER=openrouter

# API Keys
export OPENROUTER_API_KEY=sk-or-...
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=AIza...

# Ollama
export OLLAMA_HOST=http://localhost:11434

# Database
export MOOAID_DB_PATH=/path/to/database.db

# API
export MOOAID_PORT=8001
export MOOAID_HOST=0.0.0.0
```

### Docker Environment

For Docker deployments, use `.env` file:

```bash
# .env
MOOAID_PORT=8000
MOOAID_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
OLLAMA_HOST=http://ollama:11434
```

---

## Database Configuration

### SQLite (Default)

```yaml
database:
  path: "./mooaid.db"
```

### Custom Path

```yaml
database:
  path: "/var/lib/mooaid/mooaid.db"
```

---

## API Configuration

### Change Port

```yaml
api:
  host: "0.0.0.0"
  port: 8080
```

### Bind to Specific Interface

```yaml
api:
  host: "127.0.0.1"
  port: 8000
```

---

## Logging Configuration

### Change Log Level

```yaml
logging:
  level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

---

## Provider Comparison

| Provider | Cost | Speed | Quality | Best For |
|----------|------|-------|---------|----------|
| **OpenRouter** | Pay-per-use | Fast | High | Most users |
| **Ollama** | Free | Medium | Medium | Privacy, offline |
| **OpenAI** | Pay-per-use | Fast | High | GPT models |
| **Gemini** | Free tier | Fast | High | Google ecosystem |

---

## Switching Providers

### Via CLI

```bash
mooaid config provider ollama
mooaid config model llama3
```

### Via API

```bash
curl -X PUT http://localhost:8000/config \
  -H "Content-Type: application/json" \
  -d '{"provider": "ollama", "ollama_model": "llama3"}'
```

### Via Config File

Edit `config.yaml` and restart the server.

---

## Best Practices

1. **Start with OpenRouter** - Easy setup, multiple models
2. **Use Ollama for development** - Free, no API limits
3. **Set API keys via environment** - Don't commit secrets
4. **Backup your database** - Contains all your profiles
5. **Use specific models** - Don't rely on defaults

---

## Troubleshooting

### "Invalid provider"

Check available providers:
```bash
mooaid config show
```

### "API key required"

Set your API key:
```yaml
openrouter:
  api_key: "sk-or-..."
```

### "Connection refused"

For Ollama, ensure it's running:
```bash
ollama serve
```

### "Model not found"

Pull the model (Ollama):
```bash
ollama pull llama3
```

---

## Next Steps

- [[Profile Builder]] - Build your profile
- [[CLI Usage]] - Command-line interface
- [[Docker Deployment]] - Container deployment
