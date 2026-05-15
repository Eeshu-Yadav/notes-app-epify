# Notes App

A multi-user notes service built for the Epify Intern Engineering assignment.
REST API with JWT auth, sharing, public share links, and a clean web UI.

[![Backend](https://img.shields.io/badge/backend-live-success)](https://notes-app-76mt.onrender.com/about)
[![Frontend](https://img.shields.io/badge/frontend-live-success)](https://notes-app-epify.vercel.app)
[![Tests](https://img.shields.io/badge/tests-35%20passing-success)](#tests)
[![License](https://img.shields.io/badge/license-MIT-blue)](#)

## Live URLs

| | URL |
|---|---|
| **Backend (submit URL)** | https://notes-app-76mt.onrender.com |
| Frontend | https://notes-app-epify.vercel.app |
| OpenAPI schema (JSON) | https://notes-app-76mt.onrender.com/openapi.json |
| Swagger UI | https://notes-app-76mt.onrender.com/docs/ |
| `/about` endpoint | https://notes-app-76mt.onrender.com/about |

> Render's free tier sleeps after ~15 min idle — the first request takes ~30s to wake. Subsequent requests are fast.

## Features

**Required (assignment spec)**
- Email + password registration and JWT login
- CRUD on notes (title, content, timestamps)
- Owner-only access to one's own notes
- Share a note with another user by email
- `GET /openapi.json` documents the API
- `GET /about` returns identity + feature list

**Custom feature** — Public Share Links
- Generate an unguessable tokenized URL for any note
- Anyone with the link can read the note without authentication
- Rotate or revoke the link without deleting the note

**Stretch goals — all implemented**
- Pagination on `GET /notes` (`?page=`, `?page_size=`, max 100)
- Full-text search: `GET /search?q=keyword`
- Dockerfile + docker-compose for local container runs
- Full React frontend (Tailwind + shadcn/ui)
- Bonus UX: pinning, color labels, tags, edit-permission sharing

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend framework | Django 5 + DRF | Batteries-included: ORM, migrations, admin, auth |
| Auth | `djangorestframework-simplejwt` | Stateless JWT, matches assignment spec |
| API schema | `drf-spectacular` | Generates a real OpenAPI 3 schema at `/openapi.json` |
| Database (prod) | PostgreSQL 16 (Render) | Free, managed, supports JSON + full-text |
| Database (dev) | SQLite | Zero-setup local dev — auto-fallback |
| Frontend | Vite + React (JSX) + Tailwind v3 + shadcn/ui | Fast build, clean Notion/Keep-style UI |
| HTTP client | axios | Interceptor-based JWT injection |
| Hosting | Render (backend) + Vercel (frontend) | Free tiers, CLI-deployable |

## Architecture

```
frontend (Vercel, static)            backend (Render, gunicorn)
┌─────────────────────────┐          ┌─────────────────────────┐
│ Vite + React SPA        │  HTTPS   │ Django + DRF            │
│ axios → /api endpoints  │ ───────► │ JWT auth, permissions   │
│ Tailwind + shadcn/ui    │          │ Pagination + search     │
└─────────────────────────┘          └────────────┬────────────┘
                                                  │
                                                  ▼
                                         ┌─────────────────┐
                                         │  Postgres 16    │
                                         │  (Render free)  │
                                         └─────────────────┘
```

## Run locally

**Backend** (Python 3.12, port 8000):
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env             # uses SQLite if DATABASE_URL is unset
python manage.py migrate
python manage.py runserver
```

**Frontend** (Node 20+, port 5173):
```bash
cd frontend
npm install
cp .env.example .env             # set VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

**With Docker** (Postgres + backend):
```bash
cd backend
docker compose up --build
docker compose run --rm migrate   # applies migrations on demand
```

## Tests

```bash
cd backend && python manage.py test
```

35 tests covering registration, login, CRUD, sharing edge cases (self-share, non-existent user, idempotency), public links (creation, revoke, expiry, view count), search, and pagination.

## API reference

All endpoints live at the root. Auth uses `Authorization: Bearer <access_token>`.

| Method | Path | Auth | Purpose |
|---|---|:---:|---|
| POST | `/register` | | Create account |
| POST | `/login` | | Get JWT |
| GET | `/me` | ✓ | Current user |
| GET | `/notes` | ✓ | List (paginated, filterable) |
| POST | `/notes` | ✓ | Create |
| GET | `/notes/{id}` | ✓ | Retrieve |
| PUT/PATCH | `/notes/{id}` | ✓ | Update |
| DELETE | `/notes/{id}` | ✓ | Delete |
| POST | `/notes/{id}/share` | ✓ | Share by email |
| POST | `/notes/{id}/unshare` | ✓ | Revoke share |
| POST | `/notes/{id}/toggle-pin` | ✓ | Pin/unpin |
| POST/DELETE | `/notes/{id}/public-link` | ✓ | Create/revoke public link |
| GET | `/public/notes/{token}` | | Anon read via token |
| GET | `/tags` | ✓ | List user's tags |
| GET | `/search?q=` | ✓ | Full-text search |
| GET | `/about` | | Identity + features |
| GET | `/openapi.json` | | OpenAPI 3 spec |
| GET | `/docs/` | | Swagger UI |
| GET | `/health` | | Liveness probe |

## Project layout

```
.
├── backend/                # Django 5 + DRF
│   ├── accounts/           # Custom user (email PK), auth views
│   ├── notes/              # Notes, sharing, public links, tags
│   ├── core/               # /about, /search, /health
│   ├── notesapp/           # Settings, root urls, pagination
│   ├── Dockerfile          # Multi-stage build
│   ├── docker-compose.yml
│   ├── render.yaml         # Render blueprint
│   ├── build.sh            # collectstatic + migrate
│   └── requirements.txt
├── frontend/               # Vite + React + Tailwind + shadcn/ui
│   ├── src/
│   │   ├── pages/          # Login, Register, Dashboard, PublicNote
│   │   ├── components/     # NoteCard, ShareDialog, PublicLinkDialog
│   │   ├── components/ui/  # shadcn primitives
│   │   └── lib/            # api client, auth helpers
│   └── vercel.json
└── README.md
```

See [`backend/README.md`](backend/README.md) and [`frontend/README.md`](frontend/README.md) for module-level details.
