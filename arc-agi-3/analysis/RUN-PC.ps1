param(
    [int]$NodeCap = 20000,
    [double]$Seconds = 90,
    [string]$Only = '',
    [string]$Output = ''
)

$ErrorActionPreference = 'Stop'
$arcRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $arcRoot '.venv-local/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Missing local Python environment at $pythonPath"
}
& cargo build --release --manifest-path (Join-Path $arcRoot 'rust/Cargo.toml')
if ($LASTEXITCODE -ne 0) { throw 'Rust build failed' }

# Sixteen independent game processes. Each FFI single-frame call is serial.
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:RAYON_NUM_THREADS = '1'
if (-not $Output) {
    $Output = Join-Path $PSScriptRoot ('sweep-rust-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.jsonl')
}
$sweepArgs = @(
    (Join-Path $PSScriptRoot 'sweep2.py'), '--backend', 'rust', '--workers', '16',
    '--games-dir', (Join-Path $arcRoot 'games/environment_files'),
    '--node-cap', "$NodeCap", '--sec-cap', "$Seconds", '--frontier-cap', '2000',
    '--out', $Output
)
if ($Only) { $sweepArgs += @('--only', $Only) }
& $pythonPath @sweepArgs
if ($LASTEXITCODE -ne 0) { throw 'Game sweep failed' }
