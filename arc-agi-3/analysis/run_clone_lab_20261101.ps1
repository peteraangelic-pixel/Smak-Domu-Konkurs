$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
# Avoid competing 16-worker pools; finish the already-authorized evolution first.
if (Get-Process -Id 34868 -ErrorAction SilentlyContinue) {
    Write-Output 'Waiting for existing CPU evolution PID34868; no duplicate worker pool.'
    Wait-Process -Id 34868 -ErrorAction SilentlyContinue
}
$arcPython = Join-Path $PSScriptRoot '../.venv-local/Scripts/python.exe'
& $arcPython -X utf8 finalize_exhausted_search.py
if ($LASTEXITCODE -ne 0) { throw 'Exhausted search finalization failed' }
& $arcPython -X utf8 validate_fast_clones.py --workers 16 --out clone-validation-20261101/full25.jsonl
if ($LASTEXITCODE -ne 0) { throw 'Clone validation runner failed' }
& $arcPython -X utf8 benchmark_fast_tester.py --workers 16 --out clone-validation-20261101/paired25.jsonl
if ($LASTEXITCODE -ne 0) { throw 'Paired tester benchmark failed' }
Write-Output 'CLONE_LAB_COMPLETE; inspect mismatches before any promotion.'
