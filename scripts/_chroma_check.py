#!/usr/bin/env python
"""
_chroma_check.py — ChromaDB teszt, stdout-on JSON, stderr-re hibák.
Futtatás: & python _chroma_check.py  (vagy python.exe _chroma_check.py)
Kimenet: {"count": N, "status": "ok"} vagy {"error": "..."}
"""
import json
import sys
import os

VAULT = r"C:\Users\istva\Documents\gaiagent\gaiagent"
CHROMA = os.path.join(VAULT, "chromadb_data")

try:
    import chromadb
    client = chromadb.PersistentClient(path=CHROMA)
    coll = client.get_collection(name="gaiagent_readme_chunks")
    c = coll.count()
    sys.stdout.write(json.dumps({"count": c, "status": "ok"}))
except Exception as e:
    sys.stderr.write(f"CHROMA_ERROR: {e}")
    sys.stdout.write(json.dumps({"error": str(e), "status": "fail"}))
