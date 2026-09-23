Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    [!]  $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "    [X]  $msg" -ForegroundColor Red }

# 0. Escolher o interpretador
# O build usa o venv do projeto. O Python da Microsoft Store, unico da
# maquina, ja perdeu os pacotes uma vez quando a Loja atualizou o cache, e
# o build morria com um traceback obscuro. O venv nao sofre disso.
Write-Step "Verificando dependencias"
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Fail "Ambiente virtual nao encontrado em .venv\"
    Write-Host "    Crie-o com:"
    Write-Host "      python -m venv .venv"
    Write-Host "      .venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller"
    exit 1
}
Write-Ok "Usando .venv"

# O PowerShell 5.1 embrulha cada linha do stderr de um programa externo num
# ErrorRecord quando a saida e redirecionada. Com o $ErrorActionPreference =
# 'Stop' do topo isso vira erro terminante, e o script morreria aqui exibindo
# o traceback cru do Python em vez da mensagem abaixo. Por isso a preferencia
# e baixada so em volta da chamada, e o veredito sai do codigo de saida.
$eap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
# O ToString() achata os ErrorRecord em texto puro: sem ele a saida sai
# enfeitada com CategoryInfo e FullyQualifiedErrorId, escondendo a
# ultima linha do traceback, que e a unica que interessa.
$ver = & $py -m PyInstaller --version 2>&1 | ForEach-Object { $_.ToString() }
$rc = $LASTEXITCODE
$ErrorActionPreference = $eap

if ($rc -ne 0) {
    Write-Fail "PyInstaller nao esta utilizavel. O Python respondeu:"
    Write-Host ($ver | Out-String).TrimEnd()
    Write-Fail "Reinstale: .venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller"
    exit 1
}
Write-Ok "PyInstaller $ver encontrado"

# 1. Verificar logo.ico (engrenagem laranja, gerada manualmente via icon_source.png)
Write-Step "Verificando logo.ico"
if (-not (Test-Path "logo.ico")) {
    Write-Fail "logo.ico nao encontrado. Gere-o rodando: .venv\Scripts\python.exe -c ""from PIL import Image; img=Image.open('icon_source.png'); img.save('logo.ico',format='ICO',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"" "
    exit 1
}
Write-Ok "logo.ico encontrado"

# 2. Limpar builds anteriores
Write-Step "Limpando builds anteriores"
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Write-Ok "Pastas build/ e dist/ removidas"

# 3. PyInstaller
Write-Step "Empacotando com PyInstaller (aguarde alguns minutos...)"
& $py -m PyInstaller hub.spec --noconfirm
if ($LASTEXITCODE -ne 0) { Write-Fail "PyInstaller falhou."; exit 1 }
Write-Ok "Bundle gerado em dist\HubNITTRANS\"

# 4. Inno Setup
Write-Step "Compilando instalador com Inno Setup"
$innoPaths = @(
    "$env:LOCALAPPDATA\Programs\InnoSetup6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
)
$inno = $innoPaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $inno) {
    Write-Warn "Inno Setup nao encontrado. Bundle disponivel em dist\HubNITTRANS\"
    exit 0
}

New-Item -ItemType Directory -Force -Path "installer\Output" | Out-Null
& $inno "installer\setup.iss"
if ($LASTEXITCODE -ne 0) { Write-Fail "Inno Setup falhou."; exit 1 }

# 5. Resultado
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  BUILD CONCLUIDO COM SUCESSO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Instalador: installer\Output\Setup_HubNITTRANS_v5.2.exe"
Write-Host "  Bundle    : dist\HubNITTRANS\"
Write-Host ""