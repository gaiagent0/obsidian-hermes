#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
local_rest_api_discovery.py
Felfedezi a Local REST API v3.6.2 összes elérhető végpontját.
Eredmény mentve: rest_api_endpoints.json, rest_api_discovery.json
"""

import requests
import json
import sys

BASE = "https://127.0.0.1:27124"
# Token az Obsidian Local REST API Settings > Security > API Key alól
TOKEN = "bb759dfd4da8475219fe35e62c12c9ea32b90a50828a16598ed3bb5d9f79dcd5"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.verify = False
session.headers.update(HEADERS)

endpoints = [
    ("GET",  "/",                      None),
    ("GET",  "/vault/",                None),
    ("GET",  "/vault/folders",         None),
    ("GET",  "/vault/file/README.md",  None),
    ("GET",  "/tags",                  None),
    ("GET",  "/metadata",              None),
    ("GET",  "/active-file",           None),
    ("GET",  "/daily-notes",           None),
    ("GET",  "/api/v0/vault",          None),
    ("GET",  "/api/v1/vault",          None),
    ("GET",  "/api/v2/vault",          None),
    ("POST", "/search",                {"query": "snapshot"}),
    ("POST", "/api/v0/search",         {"query": "snapshot"}),
    ("POST", "/api/v1/search",         {"query": "snapshot"}),
]

results = {"success": [], "failed": []}

for method, path, body in endpoints:
    url = f"{BASE}{path}"
    try:
        resp = session.get(url, timeout=5) if method == "GET" else session.post(url, json=body, timeout=5)
        status = resp.status_code
        text = resp.text[:200]
        if status < 400:
            results["success"].append({"method": method, "path": path, "status": status, "preview": text[:150]})
            print(f"  OK  {method:4s} {path:40s} -> {status}")
        else:
            results["failed"].append({"method": method, "path": path, "status": status})
            print(f"  !!  {method:4s} {path:40s} -> {status}")
    except Exception as e:
        results["failed"].append({"method": method, "path": path, "status": "ERR", "error": str(e)[:60]})
        print(f"  ERR {method:4s} {path:40s} -> {e}")

print(f"\nOK: {len(results['success'])}  FAIL: {len(results['failed'])}")

out_dir = r"C:\Users\istva\workspace\obsidian-hermes"
for fname in ["rest_api_endpoints.json", "rest_api_discovery.json"]:
    with open(f"{out_dir}\\{fname}", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Saved: {fname}")
