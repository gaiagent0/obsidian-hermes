# Obsidian-Hermes RAG Workspace — Runbook

**Verzió:** 2.0.0 | **Frissítve:** 2026-05-14 | **Platform:** Windows 10 AMD64

---

## Cél

Az Obsidian vault és a Hermes Agent közötti **RAG integráció** infrastruktúrája.
A gaiagent projektportfólió dokumentációja természetes nyelvről lekérdezhető Hermesen keresztül.

---

## Architektúra

```
Obsidian Vault (C:/Users/istva/Documents/gaiagent/gaiagent/)
  12 projekt mappa, mindegyikben README.md
        │  direct disk read
        ▼
gaiagent_readme_indexer.py
  tiktoken cl100k_base chunking (max 500 token)
  Ollama nomic-embed-text embedding
        │
        ▼
ChromaDB PersistentClient
  collection: gaiagent_readme_chunks
  50 chunk / ~750 KB SQLite
        │  cosine similarity
        ▼
gaiagent_vault.py (5 Hermes tool)
  gaiagent_vault_query    — RAG keresés
  gaiagent_vault_context  — kontextus szöveg
  gaiagent_vault_sources  — indexelt fájlok
  gaiagent_vault_status   — státusz
  gaiagent_vault_reindex  — újraindexelés
        │
        ▼
Hermes Agent (Discord / Telegram / CLI)
```

---

## Jelenlegi állapot

| Komponens | Verzió | Állapot | Megjegyzés |
|-----------|--------|---------|------------|
| Ollama | 0.23.4 | OK | Port 11434, 17 modell |
| nomic-embed-text | latest | OK | Embedding modell |
| ChromaDB | 1.5.9 | OK | PersistentClient, 50 chunk |
| RAG Skill | gaiagent_vault.py | OK | 5 tool, működik |
| REST API | v3.6.2 | RÉSZLEGES | Csak /vault/ + /tags |
| MCP bridge | — | NINCS | REST API túl korlátozott |

---

## Obsidian Local REST API v3.6.2 — valódi állapot

**Működő endpointok:**
- `GET /` — plugin manifest
- `GET /vault/` — fájl/mappa lista
- `GET /tags` — cimkék

**NEM működő endpointok:**
- `GET /vault/file/{path}` — 404
- `POST /search` — 400 invalid Content-Type
- `/active-file`, `/metadata`, `/daily-notes` — 404

**Miért?** A v3.x plugin struktúrája megváltozott. Ez plugin-korlátozás, nem konfigurációs hiba.

> A RAG pipeline ettől független — direct disk read + ChromaDB.

---

## Gyorsstart

```powershell
# RAG keresés (azonnal működik)
hermes chat "/tool gaiagent_vault_query --query 'snapdragon modellek'"

# Újraindexelés (ha vault változott)
& "C:\Users\istva\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" `
  "C:\Users\istva\Documents\gaiagent\gaiagent\gaiagent_readme_indexer.py"

# Diagnosztika
cd C:\Users\istva\workspace\obsidian-hermes
.\scripts\setup.ps1
```

---

## Modellválasztás

| Feladat | Modell | Indoklás |
|---------|--------|-----------|
| Embedding | nomic-embed-text | Gyors, jó minőség |
| Összefoglalás | qwen2.5:7b | Gyors, jó követés |
| Komplex kérdések | deepseek-r1:8b | Gondolkodó modell |
| Könnyű kérdések | llama3.2:3b | Kis és gyors |

---

## Ismert hibák (régi repo)

A `chunk_and_index.py` / `chunk_and_index2.py` fájlokban **PATH hiba** van:
`r"C:\\Users\\..."` → négy backslash → hibás elérési út Windows-on.

**Megoldás:** Használd a `vault-scripts/gaiagent_readme_indexer.py`-t (forward slash, hibamentes).

---

## REST API alternatívák

**Opció A — régi plugin (ajánlott ha kell REST):**
Töröld `.obsidian/plugins/local-rest-api/` mappát,
telepítsd a v0.8.x verziót: https://github.com/obsidianmd/obsidian-local-rest-api/releases

**Opció B — jelenlegi RAG (ajánlott):**
50 chunk ChromaDB-ben, Ollama embedding + inference, teljesen offline.

---

## Változások

| Dátum | Verzió | Esemény |
|-------|--------|---------|
| 2026-05-16 | 2.0.1 | GitHub repoba migrálva |
| 2026-05-14 | 2.0.0 | REST API audit, korlátok feltérképezve, RAG pipeline működőképes |
| 2026-05-14 | 1.0.0 | Workspace létrehozva |
