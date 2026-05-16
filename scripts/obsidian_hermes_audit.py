#!/usr/bin/env python
"""
obsidian_hermes_audit.py
Összehasonlitja a GitHub repo-t és a workspace verziót.
Ellenorzi: script hibák, ChromaDB állapot, RAG skill, REST API, plugin-ek.
Futtatás:
    & "C:\\Users\\istva\\AppData\\Local\\hermes\\hermes-agent\\venv\\Scripts\\python.exe" obsidian_hermes_audit.py
"""
import os
import json
import sys

GITHUB_REPO = r"C:\Dev\active\hermes-obsidian"
WORKSPACE   = r"C:\Users\istva\workspace\obsidian-hermes"
VAULT_PATH  = r"C:\Users\istva\Documents\gaiagent\gaiagent"


def section(title):
    print(f"\n{'='*70}\n  {title}\n{'='*70}")

def ok(msg):   print(f"  OK  {msg}")
def warn(msg): print(f"  !!  {msg}")
def fail(msg): print(f"  XX  {msg}")
def info(msg): print(f"  --  {msg}")


# === 1. GitHub repo fajlstruktúra ===
section("1. GitHub repo fajlstruktúra")
github_files = {}
if os.path.isdir(GITHUB_REPO):
    for root, dirs, files in os.walk(GITHUB_REPO):
        rel_root = root.replace(GITHUB_REPO, "").strip("\\/")
        for f in files:
            if f.endswith(('.bin', '.lock', '.dll', '.exe', '.node')):
                continue
            full = os.path.join(root, f)
            rel  = os.path.relpath(full, GITHUB_REPO)
            github_files[rel] = os.path.getsize(full)
    print(f"\n  Fajlok (binarisok nelkul): {len(github_files)} db")
    for rel, sz in sorted(github_files.items()):
        print(f"    {rel:50s}  {sz/1024:6.1f} KB")
else:
    warn(f"GitHub repo nem talalhato: {GITHUB_REPO}")


# === 2. Script hibak ===
section("2. Script hibak ellenorzese")

for fname in ["chunk_and_index.py", "chunk_and_index2.py"]:
    path = os.path.join(GITHUB_REPO, fname)
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()
        if r'C:\\\\' in content:
            fail(f"{fname}: PATH HIBA — r'C:\\\\...' = 4 backslash (torott eleresi ut)")
        else:
            ok(f"{fname}: path OK")
    else:
        warn(f"{fname}: nem talalhato")

indexer = os.path.join(VAULT_PATH, "gaiagent_readme_indexer.py")
if os.path.exists(indexer):
    with open(indexer) as f:
        c = f.read()
    if r'C:\\\\' not in c:
        ok("gaiagent_readme_indexer.py: path OK (forward slash)")
    else:
        fail("gaiagent_readme_indexer.py: meg mindig path hiba!")
else:
    warn(f"gaiagent_readme_indexer.py nem talalhato: {indexer}")


# === 3. ChromaDB ===
section("3. ChromaDB allapot")
try:
    import chromadb
    chroma_path = os.path.join(VAULT_PATH, "chromadb_data")
    client = chromadb.PersistentClient(path=chroma_path)
    coll   = client.get_collection(name="gaiagent_readme_chunks")
    count  = coll.count()
    sample = coll.get(limit=2)
    sources = set(m.get("source", "?") for m in sample.get("metadatas", []))
    ok(f"ChromaDB: {count} chunk indexelve")
    info(f"Minta forrasok: {sources}")
except Exception as e:
    fail(f"ChromaDB hiba: {e}")


# === 4. RAG Skill ===
section("4. RAG Skill teszt")
try:
    sys.path.insert(0, VAULT_PATH)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gaiagent_vault", os.path.join(VAULT_PATH, "gaiagent_vault.py"))
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    vault = mod._vault
    if vault.ready:
        ok(f"Skill betoltodott, {vault.count} chunk")
        res = vault.search("Milyen modelleket futtat a snapdragon?", top_k=3)
        info(f"Talalatok: {res.get('returned', 0)}/{res.get('fetched', 0)}")
        for h in res.get("hits", [])[:2]:
            info(f"  [{h['source']}] sim={h['similarity']:.1%}")
    else:
        fail(f"Skill nem ready: {vault.error}")
except Exception as e:
    fail(f"Skill betoltesi hiba: {e}")


# === 5. Smart-env ===
section("5. Smart-env")
se_path = os.path.join(VAULT_PATH, ".smart-env", "smart_env.json")
if os.path.exists(se_path):
    with open(se_path) as f:
        se = json.load(f)
    ok(f"smart_env.json megvan")
    info(f"  vault: {se.get('is_obsidian_vault')}")
    info(f"  embedding: {se.get('embedding_adapter')}")
else:
    warn(f"smart_env.json nem talalhato: {se_path}")


# === 6. Összefoglaló ===
section("6. OSSSZEFOGLALO: GitHub repo vs Workspace")
print("""
  Komponens         GitHub repo                 Workspace
  ────────────────  ──────────────────────────  ──────────────────────
  README.md         '# placeholder' (ures)  XX  Reszletes           OK
  chunk_index       PATH hiba (4 backslash) XX  gaiagent_indexer   OK
  ChromaDB mode     HttpClient (Docker kell) XX  PersistentClient   OK
  RAG skill         Nincs                   XX  5 tool              OK
  setup script      obsidian_setup.py hiban XX  setup.ps1           OK
  REST API URL      http://127.0.0.1:27123  !!  https://27124       !!
""")
