# Docker Deployment

MooAId can be deployed using Docker and Docker Compose for easy containerized deployment.

## Prerequisites

- Docker 20.10+ or Podman 4.0+
- Docker Compose 2.0+ (usually included with Docker Desktop)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/CertifiedSlop/MooAId.git
cd MooAId
```

### 2. Configure Environment

Copy the environment template:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```bash
# .env
MOOAID_PORT=8000
MOOAID_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-your-key-here
```

### 3. Start with Docker Compose

**With OpenRouter (default):**
```bash
docker compose up -d
```

**With Ollama (local models):**
```bash
docker compose --profile ollama up -d
```

### 4. Verify

```bash
curl http://localhost:8000/health
```

## Docker Compose Services

| Service | Description | Port |
|---------|-------------|------|
| `mooaid` | Main API server | 8000 |
| `ollama` | Local AI models (optional) | 11434 |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MOOAID_PORT` | API port | `8000` |
| `MOOAID_PROVIDER` | AI provider | `openrouter` |
| `OPENROUTER_API_KEY` | OpenRouter API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `GEMINI_API_KEY` | Gemini API key | - |
| `OLLAMA_HOST` | Ollama host | `http://ollama:11434` |

## Common Commands

### View Logs

```bash
docker compose logs -f mooaid
```

### Stop Services

```bash
docker compose down
```

### Rebuild After Changes

```bash
docker compose up -d --build
```

### Access Database

The database is stored in a Docker volume:

```bash
docker volume inspect mooaid_mooaid_data
```

## Building Manually

### Build Image

```bash
docker build -t mooaid:latest .
# or with podman
podman build -t mooaid:latest .
```

### Run Container

```bash
docker run -d \
  -p 8000:8000 \
  -v mooaid_data:/app/data \
  -e OPENROUTER_API_KEY=your-key \
  --name mooaid \
  mooaid:latest
```

### Run with Host Network

```bash
docker run -d \
  --network host \
  -e OPENROUTER_API_KEY=your-key \
  --name mooaid \
  mooaid:latest
```

## Using Ollama Profile

To use local Ollama models:

```bash
# Start with Ollama profile
docker compose --profile ollama up -d

# Pull a model
docker compose run --rm ollama-pull

# Use in MooAId
curl -X PUT http://localhost:8000/config \
  -H "Content-Type: application/json" \
  -d '{"provider": "ollama", "ollama_model": "llama3"}'
```

## Volume Management

### Backup Database

```bash
docker run --rm \
  -v mooaid_mooaid_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/mooaid-backup.tar.gz /data
```

### Restore Database

```bash
docker run --rm \
  -v mooaid_mooaid_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/mooaid-backup.tar.gz -C /
```

## Production Considerations

### Security

- The Dockerfile uses a non-root user
- API keys should be passed via environment variables, not config files
- Consider adding authentication for production use

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  mooaid:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Health Checks

The container includes a health check:

```bash
docker inspect --format='{{.State.Health.Status}}' mooaid
```

## Troubleshooting

### Container Won't Start

Check logs:
```bash
docker compose logs mooaid
```

### Port Already in Use

Change the port in `.env`:
```bash
MOOAID_PORT=8001
```

### Ollama Connection Failed

Ensure Ollama is running:
```bash
docker compose ps
curl http://localhost:11434/api/tags
```

## Next Steps

- [[Configuration]] - Detailed configuration options
- [[Profile Builder]] - Build your profile
- [[REST API Documentation]] - API reference
