#!/usr/bin/env python
"""
gaiagent_readme_indexer.py
Indexeli a gaiagent vault README.md fájljait ChromaDB-be Ollama embeddinggel.
PersistentClient (fájlalapú) — Docker/REST API nélkül is működik.

Futtatás:
    & "C:\\Users\\istva\\AppData\\Local\\hermes\\hermes-agent\\venv\\Scripts\\python.exe" gaiagent_readme_indexer.py

FONTOS: Ne használd a chunk_and_index.py / chunk_and_index2.py fájlokat —
azokban PATH hiba van (r"C:\\\\Users\\\\..." = 4 backslash).
"""

import os
import sys
import requests
import tiktoken
import chromadb

VAULT_PATH = r"C:\Users\istva\Documents\gaiagent\gaiagent"
CHROMA_PERSIST_DIR = os.path.join(VAULT_PATH, "chromadb_data")
OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
MAX_TOKENS = 500
COLLECTION_NAME = "gaiagent_readme_chunks"

PROJECT_DIRS = [
    "fastmcp", "homelab-ai-stack", "homelab-backup-stack",
    "homelab-core-services", "homelab-media-stack", "homelab-monitoring-stack",
    "litellm-local-config", "proxmox-cluster-hardening",
    "snapdragon-ai-stack", "windows-ai-autostart", "hu-ai-chat", "portfolio",
]


def find_project_readmes():
    files = []
    for proj in PROJECT_DIRS:
        p = os.path.join(VAULT_PATH, proj, "README.md")
        if os.path.isfile(p):
            files.append(p)
    for extra in ["README.md", "_PROJEKT_MAP.md.md"]:
        p = os.path.join(VAULT_PATH, extra)
        if os.path.isfile(p):
            files.append(p)
    return files


def chunk_text(text, max_tokens=MAX_TOKENS):
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk = encoder.decode(tokens[i:i + max_tokens])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def embed_chunk(chunk):
    try:
        resp = requests.post(OLLAMA_URL, json={"model": EMBED_MODEL, "prompt": chunk}, timeout=60)
        resp.raise_for_status()
        return resp.json().get("embedding")
    except Exception as e:
        print(f"  [HIBA] Embedding: {e}")
        return None


def main():
    print("=" * 60)
    print("GAIAGENT VAULT INDEXER")
    print("=" * 60)

    readme_files = find_project_readmes()
    print(f"\nMegtalalt README fajlok: {len(readme_files)}")
    for f in readme_files:
        print(f"   - {f.replace(VAULT_PATH + os.sep, '')}")

    if not readme_files:
        print("HIBA: Nincs README fajl!")
        sys.exit(1)

    print(f"\nChunkolás + embedding (Ollama: {EMBED_MODEL})...")
    all_embeddings, all_metadatas, all_ids = [], [], []
    total_chunks = errors = 0

    for file_path in readme_files:
        rel = file_path.replace(VAULT_PATH + os.sep, "")
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except Exception as e:
            print(f"  FIGYELEM {rel}: {e}")
            errors += 1
            continue

        chunks = chunk_text(content)
        print(f"   {rel}: {len(chunks)} chunk")

        for idx, chunk in enumerate(chunks):
            emb = embed_chunk(chunk)
            if emb is None:
                errors += 1
                continue
            doc_id = f"{rel.replace('/', '_').replace('.', '_')}_ch{idx}"
            all_ids.append(doc_id)
            all_embeddings.append(emb)
            all_metadatas.append({
                "source": rel,
                "chunk_index": idx,
                "text_preview": chunk[:150] + ("..." if len(chunk) > 150 else ""),
            })
            total_chunks += 1

    print(f"\n{total_chunks} chunk embedding kesz. ({errors} hiba)")

    print(f"\nIndexelesChromaDB-be ({CHROMA_PERSIST_DIR})...")
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    if all_embeddings:
        batch_size = 20
        for i in range(0, len(all_ids), batch_size):
            collection.add(
                ids=all_ids[i:i + batch_size],
                embeddings=all_embeddings[i:i + batch_size],
                metadatas=all_metadatas[i:i + batch_size],
            )
            print(f"   ... {min(i + batch_size, len(all_ids))}/{len(all_ids)}")

        print(f"\nOK: {len(all_embeddings)} chunk indexelve -> \"{COLLECTION_NAME}\"")
        count_result = collection.count()
        print(f"   Ellenorzes: {count_result} dokumentum a gyujtemenyeben")
    else:
        print("HIBA: Nincs mit indexelni!")

    print("\n" + "=" * 60)
    print("OSSZEFO GLALAS")
    print(f"   Olvasott fajlok:   {len(readme_files)}")
    print(f"   Generalt chunkök:  {total_chunks}")
    print(f"   Hibak:             {errors}")
    print(f"   Tarolás:           {CHROMA_PERSIST_DIR}")
    print("=" * 60)
    return total_chunks


if __name__ == "__main__":
    main()
