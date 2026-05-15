# notes-app

Notes App assignment for Epify. A multi-user note manager with sharing,
tagging, search, and public read-only share links.

## Stack

- **Backend** — Django 5, DRF, SimpleJWT, drf-spectacular. Postgres in prod
  (SQLite locally). Deployed on Render.
- **Frontend** — React, Vite, Tailwind CSS, shadcn/ui. Deployed on Vercel.

## Live URLs

| | URL |
|---|---|
| Frontend | `<TBD>` |
| Backend API | `<TBD>` |
| API docs | `<TBD>/docs/` |

## Run locally

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

See [`backend/README.md`](backend/README.md) and
[`frontend/README.md`](frontend/README.md) for details, environment
variables, tests, and deployment notes.
