# obsidian-hermes

**Obsidian vault RAG integration for Hermes AI**

Connects a local Obsidian vault to [Hermes](https://hermes.sh) via a semantic search pipeline — direct disk read → **ChromaDB** (nomic-embed-text) → **Ollama** inference. No dependency on the Obsidian Local REST API for file content. Works fully offline.

---

## Architecture

```
Obsidian Vault (.md files)
        │  direct disk read
        ▼
gaiagent_readme_indexer.py
  ├─ tiktoken chunking (≤500 tokens, cl100k_base)
  └─ Ollama nomic-embed-text embedding
        │
        ▼
ChromaDB PersistentClient (SQLite)
  collection: gaiagent_readme_chunks
  ~50 chunks / 12 README files
        │  cosine similarity
        ▼
gaiagent_vault.py  ←─── 5 Hermes skill tools
        │
        ▼
Hermes Agent (Discord / Telegram / CLI)
```

---

## Repo Structure

```
obsidian-hermes/
├── README.md
├── .gitignore
├── workspace.json                       ← full config (paths, tokens, status)
├── docs/
│   └── runbook.md                       ← architecture, setup, troubleshooting
├── scripts/
│   ├── setup.ps1                        ← PowerShell diagnostic (all components)
│   ├── _chroma_check.py                 ← ChromaDB JSON health check
│   ├── _rag_check.py                    ← RAG pipeline JSON health check
│   ├── local_rest_api_discovery.py      ← REST API endpoint discovery
│   └── obsidian_hermes_audit.py         ← GitHub repo vs workspace audit
├── vault-scripts/
│   ├── gaiagent_readme_indexer.py       ← canonical indexer (no PATH bugs)
│   └── gaiagent_vault.py                ← RAG skill (5 Hermes tools)
└── hermes-skills/
    ├── integration-obsidian-vault-memory/SKILL.md
    ├── integration-obsidian-vault-rag/SKILL.md
    └── note-taking-obsidian/SKILL.md
```

---

## Quick Start

### 1. Prerequisites

```powershell
# Ollama running with embedding model
curl http://localhost:11434/api/tags
ollama pull nomic-embed-text

# Python deps (Hermes venv)
pip install chromadb tiktoken requests
```

### 2. Index the vault

```powershell
& "C:\Users\istva\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" `
  "C:\Users\istva\Documents\gaiagent\gaiagent\gaiagent_readme_indexer.py"
```

Expected: `50 chunks indexed into "gaiagent_readme_chunks"`

### 3. Verify

```powershell
cd C:\Users\istva\workspace\obsidian-hermes
.\scripts\setup.ps1
```

### 4. Query from Hermes

```bash
/tool gaiagent_vault_query --query "Milyen modelleket futtat a snapdragon-ai-stack?"
/tool gaiagent_vault_context --query "backup stratégia" --n_results 3
/tool gaiagent_vault_sources
/tool gaiagent_vault_status
/tool gaiagent_vault_reindex
```

---

## Component Status

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| Ollama | 0.23.4 | ✅ | Port 11434, 17 models |
| nomic-embed-text | latest | ✅ | Embedding model |
| ChromaDB | 1.5.9 | ✅ | PersistentClient, SQLite, 50 chunks |
| RAG Skill | gaiagent_vault.py | ✅ | 5 tools, working |
| Obsidian REST API | v3.6.2 | ⚠️ | Only `/`, `/vault/`, `/tags` — file read broken |
| MCP bridge | — | ⬜ | Not registered (REST API too limited) |

---

## Known Issues & Decisions

### ❌ Local REST API v3.6.2 limitations
`/vault/file/*` and `/search` return 404 on this version. The RAG pipeline uses **direct disk read** as a workaround — it does not depend on the REST API.

To get a fully-working REST API: downgrade the plugin to v0.8.x.

### ❌ Old indexer scripts (do not use)
`chunk_and_index.py` and `chunk_and_index2.py` in the original GitHub repo contain a **critical PATH bug**: `r"C:\\Users\\..."` produces four backslashes on Windows. Use `vault-scripts/gaiagent_readme_indexer.py` instead.

### ✅ ChromaDB: PersistentClient
Docker ChromaDB is not needed. `PersistentClient` stores to local SQLite and survives restarts. Do not mix with `HttpClient` (incompatible storage format).

---

## Environment

| Item | Value |
|------|-------|
| Vault root | `C:/Users/istva/Documents/gaiagent/gaiagent` |
| ChromaDB | `{vault}/chromadb_data/chroma.sqlite3` |
| Collection | `gaiagent_readme_chunks` |
| Embedding | `nomic-embed-text` @ `localhost:11434` |
| Inference | `qwen2.5:7b` or `deepseek-r1:8b` |
| Hermes home | `C:/Users/istva/AppData/Local/hermes` |
| Platform | Windows 10 AMD64 |

---

## License

MIT
