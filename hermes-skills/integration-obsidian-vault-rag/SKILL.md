---
name: obsidian-vault-rag
category: integration
description: RAG pipeline over an Obsidian vault using ChromaDB + Ollama. Direct disk read — no REST API dependency.
---

# Obsidian Vault RAG

RAG pipeline that reads the Obsidian vault **directly from disk**, embeds via Ollama, indexes in ChromaDB (PersistentClient).

## Architecture

```
Obsidian Vault (disk) -> direct read -> tiktoken chunking (500 tok)
  -> Ollama nomic-embed-text -> ChromaDB PersistentClient (SQLite)
  -> cosine similarity -> top-k context -> Ollama inference -> answer
```

## Environment

| Item | Value |
|------|-------|
| Vault root | `C:/Users/istva/Documents/gaiagent/gaiagent` |
| ChromaDB | `{vault}/chromadb_data/chroma.sqlite3` (~734 KB, 50 chunks) |
| Collection | `gaiagent_readme_chunks` |
| Embedding model | `nomic-embed-text` @ `localhost:11434` |
| Inference model | `qwen2.5:7b` or `deepseek-r1:8b` |
| Indexed projects | 12 README files |
| Obsidian REST API | `https://127.0.0.1:27124` (v3.6.2, partial only) |

## Tools

| Command | Description |
|---------|-------------|
| `/tool gaiagent_vault_query --query "..."` | Semantic search across vault README chunks |
| `/tool gaiagent_vault_context --query "..."` | Raw context text for downstream LLM |
| `/tool gaiagent_vault_sources` | List all indexed README files |
| `/tool gaiagent_vault_status` | Health check: chunk count, storage, Ollama |
| `/tool gaiagent_vault_reindex` | Re-runs indexer to refresh the index |

## Setup

```powershell
# 1. Ollama + model
curl http://localhost:11434/api/tags
ollama pull nomic-embed-text

# 2. Index
& "C:\Users\istva\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" `
  "C:\Users\istva\Documents\gaiagent\gaiagent\gaiagent_readme_indexer.py"

# 3. Verify
# /tool gaiagent_vault_status
```

## Known Pitfalls

### Windows Path Handling
NEVER use `r"C:\Users\..."` — raw string produces double backslashes. Use forward slashes.

### REST API v3.6.2 Limitations
Only `/`, `/vault/` (listing), `/tags` work. File content and search broken. Workaround: direct disk read.

### ChromaDB: PersistentClient vs Docker
Docker ChromaDB not needed. PersistentClient stores to SQLite, survives restarts.
Do NOT mix PersistentClient and HttpClient (incompatible storage).
