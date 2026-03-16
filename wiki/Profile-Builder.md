# Profile Builder

The Profile Builder is an AI-powered interactive tool that helps you create a comprehensive profile by asking thoughtful questions and analyzing your answers.

## Overview

Instead of manually adding traits one by one, the Profile Builder:

1. Asks you 11 questions across 4 categories
2. Analyzes your answers using AI
3. Automatically extracts and saves profile data

This creates a more natural and comprehensive profile!

## Categories

| Category | Questions | What It Captures |
|----------|-----------|------------------|
| **Interests & Hobbies** | 3 | What you enjoy doing in free time |
| **Core Values** | 3 | Your fundamental beliefs and principles |
| **Personality Traits** | 3 | How you think and interact with the world |
| **Life Context** | 2 | Your background, work, and environment |

## Using the CLI

### Start the Builder

```bash
mooaid profile build default
```

Or create a new profile:

```bash
mooaid profile build myprofile
```

### Example Session

```
╔═══════════════════════════════════════════════╗
║  🧠 Welcome to the Profile Builder            ║
╠═══════════════════════════════════════════════╣
║  Building profile: default                    ║
║                                               ║
║  I'll ask you 11 questions across 4 categories║
║  • Interests & Hobbies (3 questions)          ║
║  • Core Values (3 questions)                  ║
║  • Personality Traits (3 questions)           ║
║  • Life Context (2 questions)                 ║
║                                               ║
║  Answer honestly - there are no wrong answers!║
║  Type 'skip' to skip a question.              ║
║  Type 'quit' to exit early.                   ║
╚═══════════════════════════════════════════════╝

Category 1/4: Interests & Hobbies
Question 1/11

What hobbies or activities do you enjoy in your free time?

> I love reading science fiction novels and hiking on weekends

✓ Got it! You enjoy creative and outdoor activities.

...
```

### Commands During Session

| Command | Action |
|---------|--------|
| Type your answer | Submit your response |
| `skip` or `s` | Skip the current question |
| `quit` or `exit` | Exit early and save partial data |

## Using the Web UI

1. Open `http://localhost:8000/ui`
2. Navigate to **Profiles** tab
3. Click the **Personality Builder** banner
4. Answer the AI-generated questions
5. Your profile is automatically saved

## Using the REST API

### Start Session

```bash
curl -X POST http://localhost:8000/profile-builder/start \
  -H "Content-Type: application/json" \
  -d '{"profile_name": "myprofile"}'
```

Response:
```json
{
  "session_id": "abc123...",
  "profile_name": "myprofile"
}
```

### Get Question

```bash
curl -X POST http://localhost:8000/profile-builder/{session_id}/question
```

Response:
```json
{
  "question": "What hobbies do you enjoy?",
  "category": "Interests & Hobbies",
  "question_number": 1,
  "total_questions": 11,
  "progress_percent": 0
}
```

### Submit Answer

```bash
curl -X POST http://localhost:8000/profile-builder/{session_id}/answer \
  -H "Content-Type: application/json" \
  -d '{"answer": "I love reading and hiking"}'
```

Response:
```json
{
  "summary": "Person enjoys intellectual and outdoor activities",
  "extracted": {
    "preferences": ["reading", "hiking"],
    "values": [],
    "personality": [],
    "context": []
  },
  "progress": {...}
}
```

### Complete Session

```bash
curl -X POST http://localhost:8000/profile-builder/{session_id}/complete
```

### Cancel Session

```bash
curl -X DELETE http://localhost:8000/profile-builder/{session_id}
```

## Tips for Best Results

1. **Be honest and authentic** - The AI analyzes your actual words
2. **Provide detailed answers** - More context = better profile extraction
3. **Don't overthink** - Your natural responses reveal the most
4. **Skip irrelevant questions** - Type `skip` if a question doesn't resonate
5. **Review after** - Use `mooaid profile show` to review and refine

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Start     │────▶│   Generate   │────▶│   Submit    │
│   Session   │     │   Question   │     │   Answer    │
└─────────────┘     └──────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│    Save     │◀────│   Complete   │◀────│   Repeat   │
│   Profile   │     │   Session    │     │   (11x)    │
└─────────────┘     └──────────────┘     └─────────────┘
```

The AI uses two prompts:
1. **Question Generation** - Creates thoughtful, open-ended questions
2. **Psychoanalysis** - Extracts traits from your answers

## Troubleshooting

### "No API key configured"

The Profile Builder requires an AI provider. Configure one in `config.yaml`:

```yaml
provider: openrouter
openrouter:
  api_key: "sk-or-..."
```

### "Session not found"

Sessions expire. Start a new session with `/profile-builder/start`.

### Questions seem generic

The AI adapts to your answers. Provide more detail for better follow-ups.

## Next Steps

- [[CLI Usage]] - More CLI commands
- [[REST API Documentation]] - Full API reference
- [[Configuration]] - Customize settings
