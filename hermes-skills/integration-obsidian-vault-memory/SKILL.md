---
name: obsidian-vault-memory
description: >
  Integrate an Obsidian vault as a persistent memory and knowledge base
  for an AI agent (Hermes, Claude, etc.). Uses RAG over vault README
  files via ChromaDB + Ollama embeddings, with optional MCP/REST bridge.
tags: [obsidian, rag, memory, chromadb, ollama, knowledge-graph, vault]
version: "1.1.0"
created: "2026-05-14"
platform: [windows, linux, macos]
---

# Obsidian Vault as AI Memory Backend

Turn an Obsidian vault into a queryable, RAG-powered knowledge base for an AI agent.
End-to-end pattern: vault structure analysis → embedding pipeline → ChromaDB index → semantic retrieval.

## Architecture

```
Obsidian Vault (.md files)
        │  direct disk read
        ▼
gaiagent_readme_indexer.py
  tiktoken chunking (500 tok) + Ollama nomic-embed-text
        │
        ▼
ChromaDB PersistentClient (SQLite)
        │  cosine similarity
        ▼
Hermes agent / MCP / API call  →  RAG-augmented answers
```

Two integration modes:
- **Mode A — RAG pipeline**: vault files indexed into ChromaDB; agent queries vector store. Works offline.
- **Mode B — REST API bridge**: Obsidian Local REST API (port 27123/27124). Real-time reads, but v3.6.2 is limited.

## Prerequisites

| Component | Role | Verify |
|-----------|------|--------|
| Ollama >= 0.23 | Embedding generation | `curl localhost:11434/api/tags` |
| nomic-embed-text | Embedding model | `ollama pull nomic-embed-text` |
| ChromaDB | Vector store | `pip show chromadb` |
| Obsidian Local REST API | Real-time reads (optional) | Plugin enabled in Obsidian |

## Indexer Script

Canonical script: `vault-scripts/gaiagent_readme_indexer.py`

> DO NOT use `chunk_and_index.py` or `chunk_and_index2.py` — they have a critical
> PATH bug: `r"C:\\Users\\..."` produces 4 backslashes on Windows.

Run:
```powershell
& "C:\Users\istva\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" `
  "C:\Users\istva\Documents\gaiagent\gaiagent\gaiagent_readme_indexer.py"
```

## Hermes Tools

```
/tool gaiagent_vault_query    --query "Milyen modelleket futtat a snapdragon?"
/tool gaiagent_vault_context  --query "backup stratégia" --n_results 3
/tool gaiagent_vault_sources
/tool gaiagent_vault_status
/tool gaiagent_vault_reindex
```

## REST API Notes

Default port is **27123 HTTP**. The HTTPS/27124 scheme appeared in v3.x and has broken file reads.
If you need full REST API: downgrade plugin to v0.8.x.

## Common Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| PATH has 4 backslashes | Old script with `r"C:\\..."` | Use gaiagent_readme_indexer.py |
| Embedding is None | Ollama not running | `curl localhost:11434/api/tags` |
| 0 README files found | Wrong VAULT_PATH | Check the variable in the script |
| ChromaDB DeferredDocument | documents array has None | Updated `_trunc()` handles this |
| REST API returns 404 | v3.6.2 limitation | Use direct disk read (default) |
