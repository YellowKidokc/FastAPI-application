# POF 2828 Port Plan

The master API lives at `28280`. The surrounding ranges reserve nearby ports by
purpose so new APIs have a predictable home.

| Range | Name | Purpose |
| --- | --- | --- |
| `28280-28289` | core | Master API, service bridge, and local-first control plane |
| `28290-28299` | dashboards | Human-facing HTML dashboards and status pages |
| `28300-28319` | storage | SQLite, PostgreSQL, Synology, backups, and file indexing |
| `28320-28349` | intelligence | NLP, preference engine, embeddings, ranking, and memory |
| `28350-28369` | media | TTS, STT, image, video, and lossless compression workers |
| `28370-28389` | automation | Clipboard, launchers, schedulers, and background daemons |
| `28390-28409` | network | Cloudflare, tunnels, DNS, webhooks, and external bridges |
| `28410-28449` | agents | Codex/AI agent workers and experimental services |

## Current service catalog

| Port | Service | Domain | Owner | Notes |
| --- | --- | --- | --- | --- |
| `28280` | Master API | core | laptop-primary | FastAPI orchestrator and dashboard |
| `28281` | PostgreSQL proxy | storage | nas-preferred | Legacy PostgreSQL bridge health checks |
| `28282` | FIS | core | laptop-primary | Planned field intelligence service endpoint |
| `28283` | NLP Pipeline | intelligence | laptop-primary | Natural-language processing pipeline |
| `28284` | Dedup daemon | automation | any | Content de-duplication and normalization daemon |
| `28285` | TTS | media | laptop-primary | Text-to-speech worker |
| `28286` | Lossless Compression | media | any | Lossless compression utility |
| `28287` | Comms Hub | network | any | Cross-device communication hub |
| `28288` | Clipboard | automation | laptop-primary | Clipboard capture, sync, and WebSocket stream |
| `28289` | Cross-service bridge | core | any | Internal service-to-service bridge |
| `28290` | Health dashboard | dashboards | any | Human-readable status dashboard |
| `28300` | Synology API | storage | nas-primary | Synology DSM/File Station integration |
| `28301` | PostgreSQL Main | storage | nas-preferred | Primary relational database |
| `28302` | PostgreSQL Memory | storage | laptop-primary | Memory, embeddings, and assistant working data |
| `28303` | PostgreSQL Analytics | storage | nas-preferred | Reporting, event history, and metrics database |
| `28320` | Preference Engine | intelligence | laptop-primary | Preference scoring, ranking, and personalization |
| `28390` | Cloudflare Bridge | network | edge | Cloudflare tunnel, DNS, and webhook integration |
| `28410` | Codex Worker | agents | laptop-primary | Agent-side automation with constrained service token |

## Laptop and Synology rule

The intended operating model is laptop-first:

1. Probe the laptop/master API at `/health`.
2. If it responds, use the laptop service.
3. If it does not respond, start the local API process.
4. Use Synology for NAS-owned storage and backup services, not as the default
   compute host unless a service is explicitly marked `nas-primary`.

The current Windows launcher implements steps 1-3 for a local laptop boot.

Prefer the regular LAN address for the browser/dashboard:

- `192.168.1.76:28280` - friendly dashboard URL on the normal LAN
- `192.168.2.51:28280` - direct/10GbE route for NAS-side traffic when useful

The `192.168.1.100+` range is a good future reservation zone for stable service
IPs once the router/DHCP reservations are set.
