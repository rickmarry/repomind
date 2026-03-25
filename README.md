# REPOMIND (AI Workspace System)

REPOMIND is a lightweight, per-project AI assistant CLI for software development.

It adds persistent memory, git awareness, and structured AI workflows directly inside your repository.

---

## 🧠 Core Concept

REPOMIND treats AI as a stateless compute layer over a persistent project memory.

Each project has its own local memory stored in:

.repomind/
  context.md
  decisions.md
  session.log

- Git = source of truth for code  
- `.repomind/` = source of truth for project context  
- AI = reasoning layer over both  

---

## ⚙️ Features (v2)

- Per-project AI memory (`.repomind/`)
- Git diff integration
- AI-assisted planning
- Context-aware responses
- Lightweight CLI interface
- Model routing (fast vs smart tasks)

---

## 📦 Installation

From source:

pip install -e .

Set your API key:

export ANTHROPIC_API_KEY=your_key_here

---

## 🚀 Usage

### Initialize a project
repomind init

### Add context
repomind save "This project is a Go-based ingestion pipeline using Elasticsearch"

### Ask questions
repomind ask "refactor the service layer"

### Create a plan
repomind plan "optimize indexing performance"

### Add git diff context
repomind diff

### Execute a task
repomind exec "add caching layer to API responses"

---

## 📁 Project Structure

repomind/
├── repomind/               # Python package
├── pyproject.toml
├── README.md
└── .repomind/                # local memory (not committed)

---

## 🚫 Ignored files

Make sure these are in `.gitignore`:

.repomind/
.venv/
.git/
.idea/
.vscode/
.github/
.circleci/
.dockerignore
.gitignore
.pre-commit-config.yaml/
.env
__pycache__/
*.pyc
*.egg-info/

---

## 🧭 Status

Current: v2 (stable CLI foundation)

Next: v3 (IDE integration, semantic search, git intelligence upgrades)