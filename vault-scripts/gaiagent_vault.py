#!/usr/bin/env python
"""
gaiagent_vault.py — Hermes skill: Obsidian Vault RAG
====================================================
5 Hermes tool:
    /tool gaiagent_vault_query    --query "..." [--n_results N]
    /tool gaiagent_vault_context  --query "..." [--n_results N]
    /tool gaiagent_vault_sources
    /tool gaiagent_vault_status
    /tool gaiagent_vault_reindex

Elhelyezés: C:/Users/istva/Documents/gaiagent/gaiagent/gaiagent_vault.py
            (vault gyoker — innét tölti be a ChromaDB-t)
"""

import os
import sys
import chromadb
import requests
import tiktoken
import subprocess

VAULT_PATH = r"C:\Users\istva\Documents\gaiagent\gaiagent"
CHROMA_PATH = os.path.join(VAULT_PATH, "chromadb_data")
COLLECTION_NAME = "gaiagent_readme_chunks"
MAX_SNIPPET_TOKENS = 400


class VaultRAG:
    def __init__(self):
        self.ready = False
        self.error = None
        self.count = 0
        self._coll = None
        self._client = None
        try:
            self._client = chromadb.PersistentClient(path=CHROMA_PATH)
            self._coll = self._client.get_collection(name=COLLECTION_NAME)
            self.count = self._coll.count()
            self.ready = True
        except Exception as e:
            self.error = str(e)

    def _embed(self, text, model="nomic-embed-text"):
        try:
            r = requests.post(
                "http://localhost:11434/api/embeddings",
                json={"model": model, "prompt": text}, timeout=15)
            r.raise_for_status()
            return r.json().get("embedding", [])
        except Exception as e:
            self.error = f"Embedding hiba: {e}"
            return []

    @staticmethod
    def _trunc(text, max_toks=MAX_SNIPPET_TOKENS):
        if not text or not isinstance(text, str) or not text.strip():
            return ""
        enc = tiktoken.get_encoding("cl100k_base")
        toks = enc.encode(text.strip())
        if len(toks) <= max_toks:
            return text.strip()
        decoded = enc.decode(toks[:max_toks])
        cut = decoded.rfind(".")
        if cut > len(decoded) * 0.3:
            decoded = decoded[:cut + 1]
        return decoded.strip()

    def search(self, query, top_k=5):
        if not self.ready:
            return {"error": f"ChromaDB: {self.error}"}
        emb = self._embed(query)
        if not emb:
            return {"error": self.error or "Ures embedding"}
        fetch_n = min(top_k * 3, max(self.count, 1))
        try:
            raw = self._coll.query(
                query_embeddings=[emb], n_results=fetch_n,
                include=["documents", "metadatas", "distances"])
        except Exception as e:
            return {"error": f"Query hiba: {e}"}

        ids_raw = raw.get("ids", [[]])[0]
        docs    = raw.get("documents", [[]])[0]
        metas   = raw.get("metadatas", [[]])[0]
        dists   = raw.get("distances", [[]])[0]
        fallback = any(d is None for d in docs)

        hits, ctx_parts, seen = [], [], set()
        for idx in range(min(len(ids_raw), len(dists))):
            doc_id = ids_raw[idx]
            if doc_id in seen:
                continue
            seen.add(doc_id)
            dist   = float(dists[idx])
            meta   = metas[idx] if idx < len(metas) else {}
            source = meta.get("source", "?")
            sim    = 1.0 / (1.0 + dist)
            txt    = meta.get("text_preview", "") if fallback else (docs[idx] if idx < len(docs) and docs[idx] else "")
            snippet = self._trunc(txt)
            if not snippet:
                continue
            hits.append({"id": doc_id, "source": source, "similarity": sim, "distance": dist, "snippet": snippet})
            ctx_parts.append(f"[{source}]\n{snippet}")

        hits.sort(key=lambda h: h["similarity"], reverse=True)
        return {
            "query": query, "fetched": len(ids_raw),
            "returned": len(hits), "hits": hits[:top_k],
            "context": "\n\n---\n\n".join(ctx_parts[:top_k]),
        }

    def search_raw(self, query, top_k=5):
        res = self.search(query, top_k)
        if "error" in res:
            return f"HIBA: {res['error']}"
        lines = [f"Kerdes: \"{res['query']}\"",
                 f"Talalatok: {res['fetched']} -> megjelenitett: {res['returned']}", ""]
        for i, h in enumerate(res["hits"], 1):
            lines.append(f"  [{i}] {h['source']}  (sim={h['similarity']:.1%}, L2={h['distance']:.1f})")
            lines.append(f"      {h['snippet']}")
            lines.append("")
        return "\n".join(lines)

    def get_context(self, query, top_k=5):
        res = self.search(query, top_k)
        return res.get("context", res.get("error", "Nincs kontextus."))

    def list_sources(self):
        if not self.ready:
            return f"HIBA: {self.error}"
        try:
            out = self._coll.get(limit=self.count)
            sources = sorted(set(m.get("source", "?") for m in out.get("metadatas", [])))
            return "Indexelt forrasok:\n" + "\n".join(f"  - {s}" for s in sources)
        except Exception as e:
            return f"HIBA: {e}"

    def status(self):
        if not self.ready:
            return f"ChromaDB nem elerheto: {self.error}"
        return (f"Obsidian Vault RAG statusz\n"
                f"  Gyujtemeny:   {COLLECTION_NAME}\n"
                f"  Dokumentumok: {self.count}\n"
                f"  Tarolás:      {CHROMA_PATH}\n"
                f"  Ollama:       nomic-embed-text @ localhost:11434")

    def reindex(self):
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gaiagent_readme_indexer.py")
        python_exe = r"C:\Users\istva\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
        r = subprocess.run([python_exe, script], capture_output=True, text=True, timeout=180)
        self.__init__()
        return f"{r.stdout}\n{r.stderr}"


_vault = VaultRAG()


def gaiagent_vault_query(query: str, n_results: int = 5) -> str:
    """RAG kereses a gaiagent Obsidian vault-ban."""
    return _vault.search_raw(query, n_results)


def gaiagent_vault_context(query: str, n_results: int = 5) -> str:
    """Csak a kontextus szoveg (Hermes prompt-builderhez)."""
    return _vault.get_context(query, n_results)


def gaiagent_vault_sources() -> str:
    """Indexelt forrasok listaja."""
    return _vault.list_sources()


def gaiagent_vault_status() -> str:
    """RAG rendszer statusz."""
    return _vault.status()


def gaiagent_vault_reindex() -> str:
    """Ujraindexelés — frissiti a ChromaDB-t."""
    return _vault.reindex()


if __name__ == "__main__":
    print(_vault.status())
    print()
    print(_vault.search_raw("Milyen modelleket futtat a snapdragon-ai-stack NPU-n?"))
    print()
    print(_vault.list_sources())
