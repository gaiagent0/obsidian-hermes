---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault via filesystem tools.
platforms: [linux, macos, windows]
---

# Obsidian Vault — Note-taking Skill

Filesystem-first Obsidian vault operations: reading, listing, searching, creating, and editing notes.

## Vault Path

Use `OBSIDIAN_VAULT_PATH` env var (from `~/.hermes/.env` or `C:/Users/istva/AppData/Local/hermes/.env`).
Fallback: `~/Documents/Obsidian Vault`.

**Important:** File tools do not expand shell variables. Always resolve to a concrete absolute path first.

## Operations

### Read a note
Use `read_file` with the absolute path. Prefer over `cat` (provides line numbers, pagination).

### List notes
Use `search_files` with `target: "files"`, `pattern: "*.md"` under the vault path.

### Search content
Use `search_files` with `target: "content"`, `pattern: <regex>`, `file_glob: "*.md"`.

### Create a note
Use `write_file` with the absolute path and full markdown content.

### Append / edit
Use `patch` for anchored edits (stable context, e.g., after a heading).
Use `write_file` when rewriting the whole note is clearer.

## Wikilinks
Obsidian uses `[[Note Name]]` syntax. Include these when creating linked notes.

## Notes for gaiagent vault
- Vault root: `C:/Users/istva/Documents/gaiagent/gaiagent`
- 12 project folders, each with a README.md
- RAG indexing via `gaiagent_readme_indexer.py` (ChromaDB)
- For semantic search use `gaiagent_vault_query` tool instead of file search
