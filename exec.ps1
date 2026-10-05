param([int]$PointsNumber = 10000)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $pythonExecutable = 'python'
    if (Test-Path -LiteralPath '.venv/Scripts/python.exe') {
        $pythonExecutable = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    }
    if (-not (Test-Path -LiteralPath 'final-SP.zip')) {
        throw 'Gere final-SP.zip com regulator.py antes de executar.'
    }
    # Preserva o argumento vazio para exclusoes no Windows PowerShell.
    & $pythonExecutable -c "import runpy, sys; sys.argv = ['generator.py', sys.argv[1], '180', '1719304546', '1719701874', 'Distrito-SP.zip', '', '--weighted_shapefile', 'final-SP.zip']; runpy.run_path('generator.py', run_name='__main__')" $PointsNumber
    if ($LASTEXITCODE -ne 0) { throw "O gerador falhou (codigo $LASTEXITCODE)." }
} finally {
    Pop-Location
}
