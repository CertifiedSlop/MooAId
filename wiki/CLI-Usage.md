# CLI Usage

Complete guide to using the MooAId command-line interface.

## Overview

The CLI provides a convenient way to interact with MooAId from your terminal.

## Basic Commands

### Help

```bash
mooaid --help
```

### Version

```bash
mooaid version
```

---

## Opinion Commands

### Ask a Question

```bash
mooaid opinion ask "Should I learn Rust or Python?"
```

### Ask with Specific Profile

```bash
mooaid opinion ask "What laptop should I buy?" --profile work
```

### Ask with Additional Context

```bash
mooaid opinion ask "Is this a good investment?" \
  --profile personal \
  --context "considering long-term growth"
```

---

## Profile Commands

### List Profiles

```bash
mooaid profile list
```

### Create Profile

```bash
mooaid profile create default
mooaid profile create work
mooaid profile create personal
```

### Show Profile

```bash
mooaid profile show default
```

### Build Profile (Interactive)

```bash
mooaid profile build default
```

This starts the AI-powered Profile Builder that asks you 11 questions.

### Add to Profile

```bash
# Add preferences
mooaid profile add preferences "likes open source"
mooaid profile add preferences "prefers Linux" "values simplicity"

# Add values
mooaid profile add values "privacy" "transparency" "efficiency"

# Add personality traits
mooaid profile add personality "analytical" "pragmatic"

# Add context
mooaid profile add context "works as software engineer" "budget-conscious"
```

### Remove from Profile

```bash
mooaid profile remove preferences "old preference"
mooaid profile remove values "outdated value"
```

### Delete Profile

```bash
mooaid profile delete myprofile
```

---

## Configuration Commands

### Show Configuration

```bash
mooaid config show
```

### Set Provider

```bash
mooaid config provider openrouter
mooaid config provider ollama
mooaid config provider openai
mooaid config provider gemini
```

### Set Model

```bash
mooaid config model llama3 --provider ollama
mooaid config model gpt-4o --provider openai
mooaid config model anthropic/claude-3-haiku --provider openrouter
```

---

## Server Command

### Start API Server

```bash
mooaid serve
```

### Custom Host/Port

```bash
mooaid serve --host 0.0.0.0 --port 8080
```

### Enable Auto-Reload (Development)

```bash
mooaid serve --reload
```

---

## Examples

### Complete Workflow

```bash
# 1. Create and build your profile
mooaid profile build default

# 2. View your profile
mooaid profile show default

# 3. Ask a question
mooaid opinion ask "Should I use Vim or VS Code?"

# 4. Add more context based on the answer
mooaid profile add context "does lots of terminal work"

# 5. Ask again with updated profile
mooaid opinion ask "Should I use Vim or VS Code?"
```

### Multiple Profiles

```bash
# Create profiles for different contexts
mooaid profile create professional
mooaid profile add preferences "values code quality" --profile professional
mooaid profile add personality "risk-averse in production" --profile professional

mooaid profile create personal
mooaid profile add preferences "likes to experiment" --profile personal
mooaid profile add personality "curious and playful" --profile personal

# Get different perspectives
mooaid opinion ask "Should I rewrite this service in Go?" --profile professional
mooaid opinion ask "Should I rewrite this service in Go?" --profile personal
```

### Configuration Workflow

```bash
# Check current config
mooaid config show

# Switch to local Ollama
mooaid config provider ollama
mooaid config model llama3

# Ask a question (uses local model, no API key needed)
mooaid opinion ask "What's your take on microservices?"
```

---

## Output Formats

The CLI uses Rich for beautiful terminal output:

- **Panels** for important information
- **Tables** for lists
- **Colors** for success/error states
- **Progress indicators** for long operations

---

## Tips and Tricks

### Tab Completion

The CLI supports shell completion. Enable it:

```bash
# Bash
mooaid --install-completion bash

# Zsh
mooaid --install-completion zsh

# Fish
mooaid --install-completion fish
```

### Keyboard Shortcuts

- `Ctrl+C` - Cancel current operation
- `Ctrl+D` - Exit

### Environment Variables

Override config with environment variables:

```bash
export OPENROUTER_API_KEY=sk-or-...
mooaid opinion ask "Your question"
```

### Quiet Mode

For scripting, you can redirect output:

```bash
mooaid opinion ask "Question" > answer.txt 2>/dev/null
```

---

## Troubleshooting

### "Profile not found"

Create the profile first:
```bash
mooaid profile create myprofile
```

### "No API key configured"

Set your API key in config.yaml or via environment variable:
```bash
export OPENROUTER_API_KEY=sk-or-...
```

### "Provider not available"

Check available providers:
```bash
mooaid config show
```

### Command Not Found

Ensure the package is installed:
```bash
pip install -e .
```

---

## Next Steps

- [[Profile Builder]] - Interactive profile creation
- [[REST API Documentation]] - API reference
- [[Configuration]] - Configuration options
