# Pure Intellect Memory Plugin for Agent Zero

Connects Agent Zero to [Pure Intellect](https://github.com/Remchik64/pure-intellect) server for persistent hierarchical memory.

## Features

- **Persistent memory** across sessions and chat resets
- **Semantic search** — finds relevant facts by meaning, not just keywords
- **Auto recall** — automatically retrieves relevant memories before each response
- **Auto memorize** — saves conversation fragments automatically
- **Unlimited context** — no FAISS/VRAM limit, stored on disk

## Requirements

- Agent Zero v1.7+
- [Pure Intellect server](https://github.com/Remchik64/pure-intellect) running locally
- Ollama installed with at least one model

## Installation

### Option 1 — Via Agent Zero UI
```
Settings → Plugins → Add Plugin → enter GitHub URL
```

### Option 2 — Manual
```bash
cp -r _pure_intellect /path/to/agent-zero/usr/plugins/
touch /path/to/agent-zero/usr/plugins/_pure_intellect/.toggle-1
# Restart Agent Zero
```

## Configuration

### PI Server Address (depends on your setup)

| Agent Zero location | PI Server URL |
|---|---|
| Docker on Windows/Mac | `http://host.docker.internal:7860` |
| Docker on Linux | `http://172.17.0.1:7860` |
| Local (no Docker) | `http://localhost:7860` |

Set via environment variable:
```bash
export PI_SERVER=http://host.docker.internal:7860
```

Or edit `default_config.yaml` in the plugin folder.

### Agent Zero Model Configuration

**For Docker on Windows/Mac** (in Agent Zero Settings → Models):
```
Chat model:
  Provider: openai-compatible
  Base URL: http://host.docker.internal:7860/v1
  Model: pure-intellect
  API Key: pure-intellect

Utility model:
  Provider: openai-compatible  
  Base URL: http://host.docker.internal:11434/v1
  Model: qwen2.5:3b
  API Key: ollama
```

**For Docker on Linux**:
```
Chat model base URL: http://172.17.0.1:7860/v1
Utility model base URL: http://172.17.0.1:11434/v1
```

## Architecture

```
Agent Zero (Docker)
  ├── chat_model    →  PI server :7860/v1     → memory + Ollama 7b
  ├── utility_model →  Ollama :11434/v1       → qwen2.5:3b (direct)
  ├── memory_save   →  POST PI :7860/api/v1/memory/fact
  ├── memory_load   →  GET  PI :7860/api/v1/memory/search
  └── auto recall   →  GET  PI :7860/api/v1/memory/search (before each response)
```

## Pure Intellect Server

Install and start PI server on Windows:
```bash
# Download install.bat from GitHub and run it
# Or:
pip install pure-intellect
python -m pure_intellect serve --port 7860
```
