# Frequently Asked Questions (FAQ)

Common questions and answers about MooAId.

## General

### What is MooAId?

**MooAId** (My Opinion AI Daemon) is an AI-powered opinion prediction system. It analyzes your personality, preferences, values, and context to predict what your opinion would likely be on any given topic.

### How does it work?

1. You create a profile with your traits
2. You ask a question
3. The AI analyzes your profile and predicts your likely opinion
4. You get a personalized response with reasoning

### Is this a chatbot?

No! MooAId is **not a chatbot**. It's an **opinion prediction system**. It doesn't have its own opinions - it predicts yours based on your profile.

### What AI models are supported?

- **OpenRouter** - Multiple models (Claude, GPT, Llama, etc.)
- **Ollama** - Local models (Llama 3, Mistral, etc.)
- **OpenAI** - GPT-4, GPT-3.5
- **Google Gemini** - Gemini Pro, Gemini 1.5

### Is it free?

- **Ollama**: Completely free (runs locally)
- **OpenRouter**: Pay-per-use (very affordable)
- **OpenAI**: Pay-per-use
- **Gemini**: Free tier available

---

## Installation

### How do I install MooAId?

See [[Installation Guide]] for detailed steps.

Quick start:
```bash
git clone https://github.com/CertifiedSlop/MooAId.git
cd MooAId
pip install -e ".[dev]"
```

### Does it work on Windows?

Yes! MooAId works on Windows, macOS, and Linux.

### Can I run it without installing Python?

Yes! Use Docker:
```bash
docker compose up -d
```

See [[Docker Deployment]] for details.

### Do I need an API key?

- **OpenRouter/OpenAI/Gemini**: Yes, API key required
- **Ollama**: No API key needed (runs locally)

---

## Profile Builder

### What is the Profile Builder?

The Profile Builder is an AI-powered tool that asks you 11 questions to automatically create your profile. It's faster and more natural than manually adding traits.

### How long does it take?

About 5-10 minutes to answer all 11 questions.

### Can I skip questions?

Yes, type `skip` to skip any question.

### Can I edit my profile after?

Yes! Use:
```bash
mooaid profile add preferences "new preference"
mooaid profile remove values "old value"
```

### What if I don't like the questions?

You can:
1. Skip questions you don't like
2. Exit early with `quit`
3. Manually create your profile instead

---

## Usage

### How do I ask a question?

```bash
mooaid opinion ask "Should I learn Rust or Python?"
```

### Can I use different profiles?

Yes! Create multiple profiles:
```bash
mooaid profile create work
mooaid profile create personal

mooaid opinion ask "Should I use microservices?" --profile work
```

### How accurate are the predictions?

Accuracy depends on:
1. How detailed your profile is
2. How relevant your traits are to the question
3. The AI model's understanding

More detailed profiles = better predictions!

### Can it predict any opinion?

It works best for:
- Technology choices
- Lifestyle decisions
- Preference-based questions
- Value-driven topics

It's less useful for:
- Factual questions (use a search engine)
- Questions requiring expertise you don't have
- Highly emotional or sensitive topics

### Does it save my questions?

Yes! All opinion predictions are saved to the database. View with:
```bash
curl http://localhost:8000/history
```

---

## Technical

### Where is my data stored?

In a SQLite database (`mooaid.db`) in the project directory.

### Is my data private?

- **Local profiles**: Stored only on your machine
- **API requests**: Sent to your chosen AI provider
- **No data collection**: MooAId doesn't send data anywhere else

### Can I export my profile?

Yes! View and copy:
```bash
mooaid profile show default
```

Or via API:
```bash
curl http://localhost:8000/profile/default
```

### Can I use MooAId offline?

Yes! With Ollama, everything runs locally:
```yaml
provider: ollama
```

### How much does OpenRouter cost?

Typically $0.01-0.10 per question, depending on the model.

### Can I self-host?

Yes! MooAId is designed for self-hosting. See [[Docker Deployment]].

---

## Troubleshooting

### "Profile not found"

Create the profile first:
```bash
mooaid profile create default
```

### "No API key configured"

Set your API key in `config.yaml` or via environment variable.

### "Connection refused" (Ollama)

Start Ollama:
```bash
ollama serve
```

### "Model not found" (Ollama)

Pull the model:
```bash
ollama pull llama3
```

### The predictions are too generic

Add more specific traits to your profile:
```bash
mooaid profile add personality "prefers functional programming"
mooaid profile add context "building high-performance systems"
```

### The predictions are too verbose

Use a smaller/faster model:
```bash
mooaid config model llama3 --provider ollama
```

---

## Development

### How do I contribute?

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Where's the source code?

https://github.com/CertifiedSlop/MooAId

### How do I report a bug?

Create an issue on GitHub:
https://github.com/CertifiedSlop/MooAId/issues

### Can I add a new AI provider?

Yes! See the provider interface in `mooaid/core/provider_factory.py`.

---

## License

### What license is MooAId under?

MIT License - free for personal and commercial use.

### Can I use it commercially?

Yes! The MIT License allows commercial use.

### Do I need to credit MooAId?

Not required, but appreciated!

---

## Support

### I have a question not listed here

Check the other wiki pages or create an issue on GitHub!

### How do I stay updated?

Watch the repository on GitHub for updates.

---

## See Also

- [[Home]] - Main wiki page
- [[Installation Guide]] - Getting started
- [[Profile Builder]] - Create your profile
- [[CLI Usage]] - Command reference
- [[REST API Documentation]] - API reference
- [[Configuration]] - Settings guide
- [[Docker Deployment]] - Container deployment
