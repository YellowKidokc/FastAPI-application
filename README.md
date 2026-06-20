# FastAPI Application

POF 2828 is a local-first FastAPI control plane for laptop, Synology, Cloudflare,
clipboard, NLP, preference, and agent services.

## Run locally

```powershell
cd D:\GitHub\FastAPI-application
python -m pip install -r requirements.txt
python main.py
```

Open <http://127.0.0.1:28280/>.

## Startup launcher

The Windows launcher checks the API first. If it is not alive, it starts
`main.py` hidden, waits for `/health`, and opens the dashboard.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-POF2828.ps1
```

To install it into the current user's Windows Startup folder:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Install-POF2828Startup.ps1
```

## Secrets

Copy `.env.example` to `.env` and keep real values only in `.env`.

`POF_MASTER_TOKEN` is the owner/admin token.
`POF_CODEX_TOKEN` is the limited service token for Codex/agent automation.

Authentication is off by default while building locally. Set
`POF_AUTH_ENABLED=true` when the API should require tokens for non-public API
routes.

## API map

- `/` - HTML dashboard
- `/health` - machine-readable health and port status
- `/services` - registered service status
- `/ports` - port ranges and planned service catalog
- `/topology` - laptop/desktop/NAS route discovery
- `/api/assistant` - structured assistant command endpoint for status, ports, topology, Postgres, Synology, and clipboard
- `/api/clips` - clipboard storage/search
- `/ws/clips` - clipboard stream

See [docs/PORT_PLAN.md](docs/PORT_PLAN.md) for the five-number port layout.

## Three PostgreSQL targets

Configure each database independently in `.env`:

```powershell
POF_POSTGRES_MAIN_DSN=postgresql://user:password@host:5432/main_db
POF_POSTGRES_MEMORY_DSN=postgresql://user:password@host:5432/memory_db
POF_POSTGRES_ANALYTICS_DSN=postgresql://user:password@host:5432/analytics_db
```

The dashboard reports each one separately as `PostgreSQL Main`,
`PostgreSQL Memory`, and `PostgreSQL Analytics`.

## Synology

This project uses the `synology-api` package for DSM/File Station integration.
The upstream project documents installation as `pip3 install synology-api` and
basic usage with `synology_api.filestation.FileStation`.

Set Synology values in `.env`; never commit the real password.
