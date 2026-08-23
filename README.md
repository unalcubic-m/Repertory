# Repertory

**Spaced repetition for recognizing classical music by ear.**

Repertory is a single-owner Django application. Its first working MVP lets you:

- import an MP3 while preserving the original file;
- identify its composer and work;
- listen to the recording and mark time ranges such as “I. Allegro moderato”;
- give each marked part a canonical typed answer and optional accepted aliases;
- study due parts from anonymous audio excerpts;
- reveal the answer and rate yourself Again, Hard, Good, or Easy;
- schedule the next review with FSRS 6.

## Learning model

A marked movement or passage is the recognition target; an excerpt is generated for each review and
is not a permanent flashcard clip.

New targets begin inside the first 60 seconds of their marked range. Good and Easy reviews expand a
learning frontier farther into that range. Excerpts are randomized inside the current frontier, so the
learner starts near the beginning while still hearing changing material. FSRS controls **when** the
target returns; a separate challenge state controls excerpt length and how far into the part it may go.

Typed answers are matched only against the configured canonical answer and aliases after deterministic
Unicode, case, whitespace, and punctuation normalization. Repertory does not use fuzzy or AI grading.

## Run it locally

Requirements:

- [`uv`](https://docs.astral.sh/uv/); it will obtain the required Python 3.13 runtime if necessary;
- Node.js 24 or another current Node release supported by TypeScript 5.9;
- a browser with MP3 playback support.

```bash
uv sync --all-groups
npm ci
npm run build
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Open `http://127.0.0.1:8000`, log in with the owner account, import an MP3, and mark at least one study
part. Registration is intentionally absent.

Development data is stored under the ignored `var/` directory:

- `var/repertory.sqlite3` — library, FSRS state, review sessions, and append-only review logs;
- `var/media/originals/` — preserved original uploads;
- `var/media/playback/` — opaque metadata-stripped playback copies.

Stop the application before making a simple local backup, then copy the database and media directory
together. Do not commit either directory.

## Quality checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy library reviews repertory
uv run pytest
npm run typecheck
uv run python manage.py check --settings=repertory.settings.test
uv run python manage.py makemigrations --check --dry-run --settings=repertory.settings.test
```

Tests generate synthetic CBR/VBR tones when FFmpeg is available and otherwise use synthetic byte streams
or mocked inspection. No personal or commercial audio is stored in the repository.

## Deploy on Render

[`render.yaml`](render.yaml) defines the first hosted deployment: a Docker web service in Frankfurt with
one worker and a 5 GB persistent disk mounted at `/var/lib/repertory`. The disk is required because both
SQLite and uploaded audio would be lost on Render's otherwise ephemeral filesystem. Render persistent
disks require a paid web-service plan.

1. In Render, create a Blueprint from this repository and select branch `agent/basic-mvp` while the MVP
   pull request remains open.
2. Confirm the workspace has payment information for the Starter service and persistent disk.
3. Review and apply the Blueprint. Render generates `DJANGO_SECRET_KEY`; never replace it with a value
   committed to Git.
4. After the first healthy deploy, open the Render Shell and run
   `.venv/bin/python manage.py createsuperuser` to create the sole owner.
5. Open the service's `https://…onrender.com` URL and sign in. Registration is absent.

The application automatically trusts the exact `RENDER_EXTERNAL_HOSTNAME`. If you later add a custom
domain, set `REPERTORY_ALLOWED_HOSTS` to that hostname before switching DNS. Comma-separated exact hosts
are supported; wildcards are intentionally not.

Render disk snapshots are useful recovery points, but they do not replace a tested application-level
SQLite/media backup. Export/restore remains follow-up MVP work, so do not treat this first deployment as
the only copy of valuable learning data or recordings.

## Current boundaries

This first slice is intentionally smaller than the complete product brief. It supports MP3 only and one
owner. Marking is based on start/end timecodes assisted by the browser audio player. Rating undo,
versioned export/restore, progress charts, PWA installation, automated silence detection, and the formal
Android/desktop seeking experiment remain follow-up work.

The first deployment target is Render, not the homelab. Its web endpoint is reachable from the public
internet, but library pages, study state, and audio remain protected by Django login.

## Project documents

- [`docs/mvp.md`](docs/mvp.md) — implemented behavior, data lifecycle, and known limitations
- [`docs/product-brief.md`](docs/product-brief.md) — complete product requirements and non-goals
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — selected architecture
- [`docs/implementation-plan.md`](docs/implementation-plan.md) — implementation decisions and status
- [`docs/roadmap.md`](docs/roadmap.md) — staged delivery beyond this first slice
- [`AGENTS.md`](AGENTS.md) — repository contribution rules

## Media boundary

Use only recordings you are allowed to use. Never commit personal recordings, commercial recordings,
databases, exports, secrets, backups, or operational logs to this public repository.
