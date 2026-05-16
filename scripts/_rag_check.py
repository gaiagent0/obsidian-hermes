#!/usr/bin/env python
"""
_rag_check.py — RAG pipeline teszt.
Futtatás: python _rag_check.py
Kimenet: {"ready": true/false, "hits": N, "best": "...", "error": "..."}
"""
import json
import sys
import os

VAULT = r"C:\Users\istva\Documents\gaiagent\gaiagent"
sys.path.insert(0, VAULT)

try:
    from gaiagent_vault import _vault
    if not _vault.ready:
        sys.stdout.write(json.dumps({"ready": False, "error": _vault.error}))
        sys.exit(0)

    result = _vault.search("Milyen modelleket futtat a snapdragon-ai-stack?", top_k=3)
    if result.get("error"):
        sys.stdout.write(json.dumps({"ready": False, "error": result["error"]}))
    else:
        best = result["hits"][0]["source"] if result["hits"] else None
        sys.stdout.write(json.dumps({
            "ready": True,
            "hits": result["returned"],
            "fetched": result["fetched"],
            "best": best
        }))
except Exception as e:
    sys.stdout.write(json.dumps({"ready": False, "error": str(e)}))
