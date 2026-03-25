# REPOMIND (AI Workspace System)

REPOMIND is a lightweight, per-project AI assistant CLI for software development.

It adds persistent memory, git awareness, and structured AI workflows directly inside your repository.

---

## 🧠 Core Concept

REPOMIND treats AI as a stateless compute layer over a persistent project memory.

Each project has its own local memory stored in:

```
.repomind/
  context.md     # codebase facts (save, diff)
  decisions.md   # plans and decisions
  session.log    # full interaction log
  history.json   # rolling conversation history (20 turns)
  config.json    # provider chain config (no keys stored)
```

- Git = source of truth for code
- `.repomind/` = source of truth for project context
- AI = reasoning layer over both

---

## ⚙️ Features

- Per-project AI memory (`.repomind/`)
- Multi-provider fallback chain — claude CLI → Anthropic API → OpenAI → Gemini
- Shared conversation history across all providers
- Git diff integration
- AI-assisted planning and execution
- One-shot provider override (`--via`)

---

## 📦 Installation

From source:

```
pip install -e .
```

With optional providers:

```
pip install -e ".[openai]"
pip install -e ".[gemini]"
pip install -e ".[all]"
```

Set API keys (only for providers you want to use):

```
export ANTHROPIC_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
export GEMINI_API_KEY=your_key_here
```

Keys are read from environment only — never stored in config files.

---

## 🚀 Usage

### Initialize a project
```
repomind init
```

### Add context
```
repomind save "This project is a Go-based ingestion pipeline using Elasticsearch"
```

### Ask questions
```
repomind ask "refactor the service layer"
```

### Force a specific provider for one call
```
repomind ask --via openai "explain this architecture"
```

### Create a plan
```
repomind plan "optimize indexing performance"
```

### Add git diff to context
```
repomind diff
```

### Execute a task
```
repomind exec "add caching layer to API responses"
```

---

## 🔗 Provider Chain

By default, repomind tries providers in this order:

```
claude_cli → anthropic_api → openai → gemini
```

Providers without a configured API key are silently skipped. On failure, the next provider in the chain is tried automatically.

### View the current chain
```
repomind fallback show
```

### Reorder the chain
```
repomind fallback set claude_cli openai gemini
```

---

## 🕑 History

Conversation history is shared across all providers and persists across sessions (rolling 20-turn window).

```
repomind history show    # view recent turns
repomind history clear   # wipe history
```
