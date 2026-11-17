# Sobe o PostgreSQL (Docker Desktop), prepara o ambiente Python,
# popula o banco e inicia o site. Equivalente ao iniciar.sh no Windows.
#
# Uso (PowerShell, na pasta do projeto):
#   powershell -ExecutionPolicy Bypass -File .\iniciar.ps1
#
# Mesmo conteudo do script embutido no iniciar.exe, com uma correcao:
# $ErrorActionPreference fica em "Continue". No Windows PowerShell 5.1,
# com "Stop", qualquer texto que o Docker ou o pip escrevam no stderr
# (ate um simples WARNING) vira erro fatal e o script morre em silencio.
# Os erros reais continuam tratados pelo $LASTEXITCODE apos cada comando.

$ErrorActionPreference = "Continue"

try {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
    $OutputEncoding = [Console]::OutputEncoding
} catch { }

# Em caso de erro, mostra a mensagem e espera o Enter, para a janela
# nao fechar antes de a pessoa conseguir ler o que aconteceu.
function Falhar {
    param([string[]]$Linhas)
    Write-Host ""
    Write-Host $Linhas[0] -ForegroundColor Red
    foreach ($linha in ($Linhas | Select-Object -Skip 1)) { Write-Host $linha }
    Write-Host ""
    try { Read-Host "Pressione Enter para fechar" | Out-Null } catch { }
    exit 1
}

$env:PYTHONUTF8 = "1"
# A raiz do projeto e a pasta onde este script esta.
$raiz = $PSScriptRoot
Set-Location -LiteralPath $raiz

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

$porta = if ($env:PORT) { [string]$env:PORT } else { "5000" }

Write-Host "============================================================"
Write-Host "  Busca de Imagens - PLN (BOW + cosseno)"
Write-Host "============================================================"

# ---------------------------------------------------------------- Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Falhar @(
        "ERRO: Docker nao encontrado.",
        "Instale o Docker Desktop: https://www.docker.com/products/docker-desktop/"
    )
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Falhar @(
        "ERRO: o Docker Desktop nao esta rodando.",
        "Abra o Docker Desktop, espere o icone ficar verde e tente de novo."
    )
}

docker inspect pgsem *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Criando o container PostgreSQL (so na primeira vez)..."
    Write-Host "Se a imagem postgres:16 ainda nao existir, o Docker vai baixa-la."
    docker run -d --name pgsem --restart unless-stopped `
        -e POSTGRES_USER=sem -e POSTGRES_PASSWORD=sem123 `
        -e POSTGRES_DB=imagens_db -p 5433:5432 postgres:16 *> $null
    if ($LASTEXITCODE -ne 0) {
        Falhar @(
            "ERRO: nao foi possivel criar o container pgsem.",
            "Verifique se a porta 5433 esta livre e se o Docker esta ativo."
        )
    }
} else {
    docker start pgsem *> $null
}

Write-Host -NoNewline "Aguardando o PostgreSQL"
$pronto = $false
for ($i = 0; $i -lt 40; $i++) {
    docker exec pgsem pg_isready -U sem -d imagens_db *> $null
    if ($LASTEXITCODE -eq 0) {
        $pronto = $true
        break
    }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 1
}
if (-not $pronto) {
    Falhar @(
        "ERRO: o PostgreSQL nao respondeu em 40 segundos.",
        "Rode: docker logs pgsem"
    )
}
Write-Host " pronto."

# ---------------------------------------------------------------- Python
$python = $null
foreach ($cmd in @("py", "python", "python3")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        & $cmd -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" *> $null
        if ($LASTEXITCODE -eq 0) {
            $python = $cmd
            break
        }
    }
}
if (-not $python) {
    Falhar @(
        "ERRO: Python 3.12+ nao encontrado.",
        "Instale em https://www.python.org/downloads/ e marque",
        "'Add python.exe to PATH' durante a instalacao."
    )
}

$venvPython = Join-Path $raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Criando ambiente Python (.venv)..."
    & $python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Falhar @("ERRO: nao foi possivel criar o ambiente virtual.")
    }
}

& $venvPython -c "import flask, psycopg2, sklearn, nltk, rapidfuzz" *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Instalando dependencias (pode demorar alguns minutos)..."
    & $venvPython -m pip install --quiet --upgrade pip
    & $venvPython -m pip install --quiet -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Falhar @(
            "ERRO: falha ao instalar as dependencias.",
            "Tente rodar manualmente:",
            "  .venv\Scripts\python.exe -m pip install -r requirements.txt"
        )
    }
}

# ---------------------------------------------------------------- Dados
Write-Host "Populando o banco e gerando as imagens de exemplo..."
& $venvPython seed.py
if ($LASTEXITCODE -ne 0) {
    Falhar @("ERRO: falha ao popular o banco.")
}

Write-Host ""
Write-Host "Abra no navegador:  http://127.0.0.1:$porta"
Write-Host "Para encerrar:      Ctrl+C"
Write-Host ""

# Abre o navegador depois de 2 segundos, sem travar o servidor.
Start-Job -ScriptBlock {
    param($url)
    Start-Sleep -Seconds 2
    Start-Process $url
} -ArgumentList "http://127.0.0.1:$porta" | Out-Null

& $venvPython -m flask --app app run --host 127.0.0.1 --port $porta

if ($LASTEXITCODE -ne 0) {
    Falhar @(
        "O servidor encerrou com erro.",
        "Se a porta $porta estiver ocupada, feche o outro processo e tente de novo."
    )
}
