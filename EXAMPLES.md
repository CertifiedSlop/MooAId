# MooAId Example Usage Guide

This guide demonstrates how to use MooAId in various scenarios.

---

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [CLI Examples](#cli-examples)
3. [REST API Examples](#rest-api-examples)
4. [Python SDK Examples](#python-sdk-examples)
5. [Use Cases](#use-cases)

---

## Initial Setup

### 1. Configure Your Provider

Edit `config.yaml` with your preferred AI provider:

**For Ollama (Local, Free):**
```yaml
provider: ollama
ollama:
  host: "http://localhost:11434"
  model: "llama3"
```

**For OpenRouter:**
```yaml
provider: openrouter
openrouter:
  api_key: "sk-or-..."
  default_model: "anthropic/claude-3-haiku"
```

**For OpenAI:**
```yaml
provider: openai
openai:
  api_key: "sk-..."
  default_model: "gpt-3.5-turbo"
```

### 2. Start the Service

```bash
# Using the CLI
mooaid serve

# Or directly with uvicorn
uvicorn mooaid.api:app --reload
```

---

## CLI Examples

### Creating a Profile

```bash
# Create your default profile
mooaid profile create default

# Or create multiple profiles for different contexts
mooaid profile create personal
mooaid profile create work
mooaid profile create tech_decisions
```

### Adding Profile Data

```bash
# Add preferences
mooaid profile add preferences "likes open source"
mooaid profile add preferences "prefers Linux over Windows"
mooaid profile add preferences "values simplicity over features"
mooaid profile add preferences "dislikes vendor lock-in"

# Add values
mooaid profile add values "privacy"
mooaid profile add values "transparency"
mooaid profile add values "efficiency"
mooaid profile add values "sustainability"

# Add personality traits
mooaid profile add personality "analytical"
mooaid profile add personality "pragmatic"
mooaid profile add personality "skeptical of marketing hype"
mooaid profile add personality "prefers data-driven decisions"

# Add context
mooaid profile add context "works as software engineer"
mooaid profile add context "budget-conscious"
mooaid profile add context "values work-life balance"
```

### Viewing Your Profile

```bash
# List all profiles
mooaid profile list

# Show profile details
mooaid profile show default
mooaid profile show work
```

### Asking Questions

```bash
# Ask a simple question
mooaid opinion ask "Should I learn Rust or Python?"

# Ask using a specific profile
mooaid opinion ask "What laptop should I buy?" --profile work

# Complex questions
mooaid opinion ask "Is it worth paying extra for a Mac over a Windows laptop?"
mooaid opinion ask "Should I contribute to open source or focus on personal projects?"
mooaid opinion ask "Is remote work better than working in an office?"
```

### Configuration

```bash
# Show current config
mooaid config show

# Switch provider
mooaid config provider ollama

# Change model
mooaid config model llama3 --provider ollama
mooaid config model gpt-4 --provider openai
```

---

## REST API Examples

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Get configuration
curl http://localhost:8000/config

# List profiles
curl http://localhost:8000/profile

# Create a profile
curl -X POST http://localhost:8000/profile \
  -H "Content-Type: application/json" \
  -d '{"name": "personal"}'

# Add preferences to profile
curl -X POST http://localhost:8000/profile/personal/add \
  -H "Content-Type: application/json" \
  -d '{"field": "preferences", "items": ["likes minimalism", "values quality"]}'

# Get a profile
curl http://localhost:8000/profile/personal

# Ask a question
curl -X POST http://localhost:8000/opinion \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Should I buy a mechanical keyboard?",
    "profile_name": "personal"
  }'

# Ask with additional context
curl -X POST http://localhost:8000/opinion \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Should I use Vim or VS Code?",
    "profile_name": "work",
    "additional_context": ["doing lots of terminal work", "need good debugging tools"]
  }'

# Update a profile
curl -X PUT http://localhost:8000/profile/personal \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": ["likes minimalism", "values quality", "prefers CLI"],
    "values": ["efficiency", "simplicity"]
  }'

# Delete a profile
curl -X DELETE http://localhost:8000/profile/personal
```

### Using Python with httpx

```python
import httpx

async def example():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Create profile
        await client.post("/profile", json={"name": "tech"})
        
        # Add preferences
        await client.post("/profile/tech/add", json={
            "field": "preferences",
            "items": ["likes performance", "prefers open source"]
        })
        
        # Ask a question
        response = await client.post("/opinion", json={
            "question": "Should I use PostgreSQL or MongoDB?",
            "profile_name": "tech"
        })
        
        result = response.json()
        print(result["predicted_opinion"])
        print(result["reasoning"])
```

### Using JavaScript/Node.js

```javascript
const axios = require('axios');

async function example() {
    const api = axios.create({ baseURL: 'http://localhost:8000' });
    
    // Create profile
    await api.post('/profile', { name: 'personal' });
    
    // Add preferences
    await api.post('/profile/personal/add', {
        field: 'preferences',
        items: ['values privacy', 'prefers self-hosting']
    });
    
    // Ask a question
    const response = await api.post('/opinion', {
        question: 'Should I use cloud services or self-host?',
        profile_name: 'personal'
    });
    
    console.log(response.data.predicted_opinion);
    console.log(response.data.reasoning);
}
```

---

## Python SDK Examples

### Direct Usage

```python
import asyncio
from mooaid.config import get_config, ConfigManager
from mooaid.profile import DatabaseManager, ProfileData
from mooaid.profile.service import ProfileService
from mooaid.core.opinion_engine import OpinionEngine
from mooaid.core.provider_factory import get_provider

async def main():
    # Initialize
    config = get_config()
    db = DatabaseManager(config.database.path)
    await db.init_db()
    profile_service = ProfileService(db)
    
    # Create or get profile
    profile = await profile_service.get_profile("default")
    if profile is None:
        profile = await profile_service.create_profile("default")
        await profile_service.add_preferences("default", ["likes open source"])
        await profile_service.add_values("default", ["privacy", "transparency"])
        await profile_service.add_personality("default", ["analytical", "pragmatic"])
    
    # Get provider and create engine
    provider = get_provider(config.provider)
    engine = OpinionEngine(provider)
    
    # Predict opinion
    result = await engine.predict(
        question="Is Rust better than Python for backend development?",
        profile=profile,
        profile_name="default"
    )
    
    print(f"Predicted Opinion: {result.predicted_opinion}")
    print(f"Reasoning: {result.reasoning}")
    
    # Cleanup
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Use Cases

### 1. Decision Support

Use MooAId to help make decisions aligned with your values:

```bash
# Career decisions
mooaid opinion ask "Should I take the FAANG job or join a startup?"

# Purchase decisions
mooaid opinion ask "Is the $3000 MacBook Pro worth it for my needs?"

# Technology choices
mooaid opinion ask "Should I use Kubernetes or Docker Swarm for this project?"
```

### 2. Consistency Checking

Verify your decisions align with your stated preferences:

```bash
# Add your stated values
mooaid profile add values "environmental sustainability"

# Check consistency
mooaid opinion ask "Should I buy an electric car or use public transport?"
```

### 3. Multi-Personality Profiles

Create profiles for different aspects of your life:

```bash
# Professional profile
mooaid profile create professional
mooaid profile add preferences "values code quality" --profile professional
mooaid profile add personality "risk-averse in production" --profile professional

# Personal profile  
mooaid profile create personal
mooaid profile add preferences "likes to experiment" --profile personal
mooaid profile add personality "curious and playful" --profile personal

# Get different perspectives
mooaid opinion ask "Should I rewrite this service in Go?" --profile professional
mooaid opinion ask "Should I rewrite this service in Go?" --profile personal
```

### 4. Team Alignment

Share your profile with team members so they can predict your decisions:

```bash
# Export your profile (manual for now)
mooaid profile show work > my_work_profile.txt

# Team member can import and ask
mooaid profile create teammate_profile
# ... add traits from my_work_profile.txt
mooaid opinion ask "Would Alex approve this PR approach?" --profile teammate_profile
```

---

## Tips for Better Predictions

1. **Be Specific**: Add detailed preferences, not just general ones
   - ✅ "prefers type safety in production code"
   - ❌ "likes good code"

2. **Add Context**: Include relevant background
   - "works in fintech industry"
   - "manages team of 5 developers"

3. **Update Regularly**: Keep your profile current as your preferences evolve

4. **Use Multiple Profiles**: Separate work, personal, and specific decision contexts

5. **Provide Context Per Question**: Use `additional_context` for situation-specific details

---

## Troubleshooting

### "Provider not configured" Error

Make sure you've set up your API keys in `config.yaml`:

```yaml
openrouter:
  api_key: "your-key-here"
```

### "Profile not found" Error

Create the profile first:

```bash
mooaid profile create myprofile
```

### Ollama Connection Error

Ensure Ollama is running:

```bash
ollama serve
# Or check if it's running
curl http://localhost:11434/api/tags
```

---

## Next Steps

- Explore the API documentation at `http://localhost:8000/docs`
- Check out the README.md for more information
- Contribute to the project on GitHub
