# Repertory

**Spaced repetition for recognizing music by ear.**

> Repertory is in the planning stage. The repository does not contain a production application yet.

Repertory will play a fresh, randomly selected excerpt from a user-provided audio recording and ask the learner to type what they hear. As recognition improves, excerpts become shorter and reviews become less frequent.

## Core learning loop

1. Import a recording and describe the musical work, movement, composer, and accepted answer aliases.
2. Repertory selects a due recognition target.
3. It plays a random excerpt without revealing the filename or metadata.
4. The learner types the answer rather than choosing from multiple-choice options.
5. Repertory reveals the canonical answer and the learner grades the review: **Again**, **Hard**, **Good**, or **Easy**.
6. FSRS determines the next review date, while a separate difficulty model adjusts future excerpt length and region difficulty.

## Key design principle

A review item represents a **piece or movement to recognize**, not one fixed audio clip. Every review should normally sample a different part of the recording so the learner recognizes the music itself rather than memorizing a particular opening.

The scheduling model and the audio-difficulty model are related but distinct:

- **Scheduling** answers: “When should this item be reviewed again?”
- **Excerpt difficulty** answers: “How much audio should the learner hear next time?”

## Selected initial architecture

- **Backend:** Python 3.13 and Django 5.2 LTS
- **Browser UI:** Django templates plus a small strict-TypeScript review/audio client
- **Scheduler:** FSRS 6 through the maintained Python implementation
- **Audio:** authenticated range playback and browser seeking first; Mutagen and FFmpeg/ffprobe where needed
- **Database:** SQLite in WAL mode for the initial single-user deployment
- **Dependency management:** `uv`
- **Runtime:** one Docker/Compose application workload; no Redis or Celery in the MVP
- **Client:** responsive, online-first, installable PWA for desktop and Android

The only approved browser-facing production URL is:

```text
https://repertory.metrekare.cloud
```

Do not substitute another subdomain or a path-prefix deployment. The URL is planned for private split DNS and the existing private Traefik ingress, reachable only from the home LAN and approved WireGuard clients. Public application exposure is not part of the initial scope.

The application will be designed so a later guarded scale-to-zero layer can stop it after inactivity and wake it on the first private request. The normal always-running deployment must be developed, measured, and accepted first.

## Initial MVP goals

- Mobile-first installable web app/PWA.
- User-supplied MP3 files, with other formats added only after compatibility testing.
- Library of composers, works/collections, movements, recordings, aliases, and recognition targets.
- Random bounded excerpts with adaptive duration and recent-region avoidance.
- Typed free-recall answers with deterministic normalization and explicit self-grading.
- FSRS 6 behind a replaceable application-owned scheduler interface.
- Review history, basic progress statistics, versioned export, and reliable backup/restore.
- Privacy-conscious self-hosting without distributing copyrighted recordings.

## Terminology

| Term | Meaning in Repertory |
| --- | --- |
| **Work** | A composition such as *The Four Seasons* or *Symphony No. 5*. A work may belong to a parent collection. |
| **Movement** | A major section inside a work, such as “I. Allegro.” |
| **Recording** | A particular performance independent of its stored audio file. |
| **Audio asset** | An original file supplied by the user and stored outside Git. |
| **Recognition target** | The work or movement expected as the typed answer. |
| **Excerpt** | The temporary segment played during one review. It is not a permanent card. |

## Project documents

- [`docs/product-brief.md`](docs/product-brief.md) — product goals, requirements, edge cases, and non-goals
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — selected initial stack, private deployment contract, and optional sleep design
- [`docs/roadmap.md`](docs/roadmap.md) — staged delivery from planning through private deployment
- [`docs/CODEX_PLANNING_PROMPT.md`](docs/CODEX_PLANNING_PROMPT.md) — implementation-planning prompt for Codex
- [`AGENTS.md`](AGENTS.md) — repository instructions for coding agents

## Media and private-data boundary

Repertory is intended to help users study audio they are legally allowed to use. Do not commit personal music files, copyrighted commercial recordings, album artwork extracted from user media, databases, review exports, credentials, environment files, backups, or private operational logs to this public repository.

Tests should generate synthetic audio or use clearly licensed fixtures whose provenance is documented.

## Status and next step

The next step is a complete architecture and implementation plan. Feature code should not be scaffolded until the planning phase resolves the explicit data model, review transaction, answer matching, audio compatibility experiment, test strategy, security model, and ordered implementation backlog.
