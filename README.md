# Busca de Imagens de Sensoriamento Remoto — PLN

Aplicação Flask de página única que responde perguntas em português sobre um
catálogo de imagens, usando PLN clássico (BOW/TF-IDF + cosseno) e PostgreSQL.

Este README é só sobre **como rodar**.

---

## Requisitos

- **Python 3.12+** (64 bits)
- **Docker** (Docker Desktop no Windows; Docker Engine no Linux)
- Portas **5433** (PostgreSQL) e **5000** (site) livres
- Internet na primeira execução (para baixar a imagem do PostgreSQL e instalar
  as dependências)

---

## Linux

```bash
cd Projeto_trio
chmod +x iniciar.sh
./iniciar.sh
```

Abra no navegador:

```text
http://127.0.0.1:5000
```

Para encerrar o site, pressione **Ctrl+C** no terminal.

---

## Windows 11

1. Instale o **Docker Desktop** e o **Python 3.12+**.
   - No Docker Desktop, habilite o **WSL2** durante a instalação.
   - No Python, marque **“Add python.exe to PATH”**.
   - Abra o Docker Desktop e espere o ícone ficar verde.
2. Na pasta do projeto, dê **dois cliques em `iniciar.exe`**.
3. Abra no navegador:

```text
http://127.0.0.1:5000
```

Também funciona pelo PowerShell:

```powershell
cd C:\caminho\para\Projeto_trio
.\iniciar.exe
```

Para encerrar o site, pressione **Ctrl+C** na janela do terminal.

> O `iniciar.exe` é autossuficiente: ele embute o script PowerShell e o executa.
> Se o SmartScreen bloquear, clique em **“Mais informações” → “Executar assim
> mesmo”**.

---

## O que o iniciador faz

1. Sobe o PostgreSQL no container `pgsem` (porta **5433**).
2. Cria o ambiente `.venv` e instala `requirements.txt`.
3. Executa `seed.py`, que recria a tabela e gera 60 imagens de exemplo.
4. Inicia o Flask em `http://127.0.0.1:5000`.

Na primeira execução, pode demorar alguns minutos: o Docker baixa a imagem do
PostgreSQL e o `pip` instala as dependências. Nas próximas, é bem mais rápido.

> **Atenção:** o `seed.py` recria a tabela a cada execução. Se você inserir
> dados manualmente, eles serão perdidos ao rodar o iniciador de novo.

---

## Mudar a porta do site

O padrão é **5000**.

Linux:

```bash
PORT=5001 ./iniciar.sh
```

Windows (PowerShell):

```powershell
$env:PORT = "5001"
.\iniciar.exe
```

Depois acesse `http://127.0.0.1:5001`.

---

## Modo manual (opcional)

Se quiser rodar etapa por etapa, sem o script. O modo manual assume que o
`.venv` já foi criado pelo iniciador pelo menos uma vez.

Na primeira vez, crie o container do banco:

```bash
docker run -d --name pgsem --restart unless-stopped \
  -e POSTGRES_USER=sem -e POSTGRES_PASSWORD=sem123 \
  -e POSTGRES_DB=imagens_db -p 5433:5432 postgres:16
```

Depois, use `docker start pgsem` nas próximas execuções.

### Linux

```bash
docker start pgsem
source .venv/bin/activate
python seed.py
flask --app app run --host 127.0.0.1 --port 5000
```

### Windows 11

```powershell
docker start pgsem
.\.venv\Scripts\Activate.ps1
python seed.py
python -m flask --app app run --host 127.0.0.1 --port 5000
```

Se o PowerShell bloquear a ativação:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

> A pasta `build/` serve apenas para recompilar o `iniciar.exe`; ela não é
> necessária para rodar o projeto.

---

## Problemas comuns

| Problema | Solução |
|---|---|
| `docker: command not found` | instale o Docker e reabra o terminal |
| `Cannot connect to the Docker daemon` | abra o Docker Desktop e espere ficar verde |
| `python` abre a Microsoft Store | instale de python.org ou use `py -3` |
| `port is already allocated` (5433) | pare o outro container/processo que usa a porta |
| `port 5000 already in use` | feche o outro Flask ou use `PORT=5001` |
| `iniciar.exe` bloqueado | “Mais informações” → “Executar assim mesmo” |
| `Permission denied` no Linux | `chmod +x iniciar.sh` |
| Erro ao instalar dependências | apague `.venv` e rode o iniciador de novo |

---

## Reset rápido

Linux:

```bash
docker rm -f pgsem
rm -rf .venv
./iniciar.sh
```

Windows 11 (PowerShell):

```powershell
docker rm -f pgsem
Remove-Item -Recurse -Force .venv
.\iniciar.exe
```
