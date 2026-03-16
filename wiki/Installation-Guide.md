# Installation Guide

This guide covers installing MooAId on different platforms.

## Prerequisites

- Python 3.10 or higher
- pip or uv for package management
- Git for cloning the repository

## Installation from Source

### 1. Clone the Repository

```bash
git clone https://github.com/CertifiedSlop/MooAId.git
cd MooAId
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

Or using uv:

```bash
uv pip install -e ".[dev]"
```

### 4. Verify Installation

```bash
mooaid --help
```

You should see the CLI help message.

## Nix Environment

If you use Nix, you can enter the development shell:

```bash
nix-shell
```

This creates an isolated environment with Python and dependencies.

## Docker Installation

For containerized deployment, see [[Docker Deployment]].

Quick start:

```bash
docker compose up -d
```

## Post-Installation

### Configure Your AI Provider

Edit `config.yaml` with your preferred provider:

**OpenRouter:**
```yaml
provider: openrouter
openrouter:
  api_key: "sk-or-..."
  default_model: "anthropic/claude-3-haiku"
```

**Ollama (Local):**
```yaml
provider: ollama
ollama:
  host: "http://localhost:11434"
  model: "llama3"
```

**OpenAI:**
```yaml
provider: openai
openai:
  api_key: "sk-..."
  default_model: "gpt-4o"
```

**Google Gemini:**
```yaml
provider: gemini
gemini:
  api_key: "AIza..."
  default_model: "gemini-pro"
```

### Create Your Profile

Use the interactive Profile Builder:

```bash
mooaid profile build default
```

Or manually:

```bash
mooaid profile create default
mooaid profile add preferences "likes open source"
mooaid profile add values "privacy"
mooaid profile add personality "analytical"
```

## Troubleshooting

### "mooaid: command not found"

Make sure the virtual environment is activated and the package is installed:

```bash
source venv/bin/activate
pip install -e .
```

### Import Errors

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Permission Errors on Linux

If you get permission errors, try:

```bash
pip install --user -e ".[dev]"
```

## Next Steps

- [[Profile Builder]] - Build your personality profile
- [[CLI Usage]] - Learn the command-line interface
- [[REST API Documentation]] - Integrate with the API
- [[Web UI]] - Use the browser interface
