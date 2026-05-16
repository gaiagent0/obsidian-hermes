#Requires -Version 5.1
<#
.SYNOPSIS
    Obsidian-Hermes RAG Workspace — Diagnosztikai script (v3)
    Ellenorzi: Ollama, ChromaDB, RAG skill, REST API, smart-env
.NOTES
    REST API: https://127.0.0.1:27124 (v3.6.2 — csak /vault/ + /tags)
    Futtatás: .\scripts\setup.ps1
#>

$ErrorActionPreference = "Continue"
$vaultPath    = "C:\Users\istva\Documents\gaiagent\gaiagent"
$hermesPython = "C:\Users\istva\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
$scriptDir    = $PSScriptRoot
$restBase     = "https://127.0.0.1:27124"
$restToken    = "bb759dfd4da8475219fe35e62c12c9ea32b90a50828a16598ed3bb5d9f79dcd5"

function Write-Section($t) {
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "  $t"        -ForegroundColor Cyan
    Write-Host $('='*60)    -ForegroundColor Cyan
}
function Ok($m)   { Write-Host "  OK  $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  !!  $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "  XX  $m" -ForegroundColor Red }
function Info($m) { Write-Host "  --  $m" }

# === 1. OLLAMA ===
Write-Section "1. OLLAMA"
try {
    $r = curl.exe -s http://localhost:11434/api/tags 2>$null | ConvertFrom-Json -EA Stop
    if ($r.models.Count -gt 0) {
        Ok "Ollama fut @ localhost:11434 ($($r.models.Count) modell)"
        $r.models | ForEach-Object { Info "     $($_.name)" }
        $eb = '{"model":"nomic-embed-text","prompt":"test"}'
        $et = curl.exe -s -X POST -H "Content-Type: application/json" -d $eb http://localhost:11434/api/embeddings 2>&1 | ConvertFrom-Json -EA SilentlyContinue
        if ($et -and $et.embedding) { Ok "nomic-embed-text embedding: OK" }
        else { Warn "nomic-embed-text embedding hiba (modell hideg?)" }
    } else { Warn "Ollama fut de nincs modell" }
} catch { Fail "Ollama nem elerheto — inditsd: C:\Users\istva\AppData\Local\Programs\Ollama\ollama.exe" }

# === 2. CHROMADB ===
Write-Section "2. CHROMADB"
$chromaPath = Join-Path $vaultPath "chromadb_data"
if (Test-Path $chromaPath) {
    $sz = (Get-ChildItem $chromaPath -Recurse | Measure-Object Length -Sum).Sum
    Info "Mappa: $chromaPath ($([math]::Round($sz/1KB,1)) KB)"
    $res = & $hermesPython "$scriptDir\_chroma_check.py" 2>&1
    try {
        $cd = ($res -split "`n" | Where-Object { $_ -match "^\{" }) -join "" | ConvertFrom-Json -EA Stop
        if ($cd.status -eq "ok") { Ok "ChromaDB: $($cd.count) chunk" }
        else { Fail "ChromaDB hiba: $($cd.error)" }
    } catch { Fail "ChromaDB nem olvasható: $res" }
} else {
    Fail "chromadb_data mappa nem talalhato: $chromaPath"
}

# === 3. RAG SKILL ===
Write-Section "3. RAG SKILL"
$ragRes = & $hermesPython "$scriptDir\_rag_check.py" 2>&1
try {
    $rd = ($ragRes -split "`n" | Where-Object { $_ -match "^\{" }) -join "" | ConvertFrom-Json -EA Stop
    if ($rd.ready) {
        Ok "RAG skill: KESZ — $($rd.hits) talalat"
        Info "  Legjobb forras: $($rd.best)"
    } else { Fail "RAG skill nem kesz: $($rd.error)" }
} catch { Warn "RAG teszt kimenet nem ertelmezhetoe: $ragRes" }

# === 4. REST API ===
Write-Section "4. OBSIDIAN LOCAL REST API (v3.6.2)"
$root = curl.exe -sk -H "Authorization: Bearer $restToken" "$restBase/" 2>&1 | ConvertFrom-Json -EA SilentlyContinue
if ($root -and $root.status -eq "OK") {
    Ok "REST API: v$($root.versions.self) / Obsidian v$($root.versions.obsidian)"
    $vl = curl.exe -sk -H "Authorization: Bearer $restToken" "$restBase/vault/" 2>&1 | ConvertFrom-Json -EA SilentlyContinue
    if ($vl -and $vl.files) { Ok "  /vault/: $($vl.files.Count) elem" }
} else {
    Warn "REST API nem elerheto ($restBase) — Obsidian fut?"
}
Warn "KORLATOKK: /vault/file/* es /search NEM mukodik (v3.6.2)"
Info "  A RAG pipeline nem fugg a REST API-tol (direct disk read)"

# === 5. SMART-ENV ===
Write-Section "5. SMART-ENV"
$sePath = Join-Path $vaultPath ".smart-env\smart_env.json"
if (Test-Path $sePath) {
    $se = Get-Content $sePath -Raw | ConvertFrom-Json
    Ok "smart_env.json megvan"
    Info "  vault: $($se.is_obsidian_vault)"
    Info "  embedding: $($se.embedding_adapter)"
} else { Warn "smart_env.json nem talalhato: $sePath" }

Write-Section "KESZ"
Info "RAG pipeline mukodik: Ollama + ChromaDB + gaiagent_vault.py"
Info "Ujraindexeles: /tool gaiagent_vault_reindex"
Info "Kereses: /tool gaiagent_vault_query --query '...'"
