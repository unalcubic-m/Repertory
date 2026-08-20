# AGENTS.md

## Mission

Build Repertory as a private, web-first application that trains recognition of musical works and movements from changing audio excerpts using typed free recall and spaced repetition.

## Read before changing anything

1. `README.md`
2. `docs/product-brief.md`
3. `docs/architecture-decisions.md`
4. `docs/roadmap.md`
5. The current issue or planning task that authorized the work

When these documents conflict, stop and make the conflict explicit rather than silently choosing a new product direction.

## Architecture boundaries

The initial architecture is deliberately small:

- Python 3.13
- Django 5.2 LTS
- Django templates for ordinary pages
- A small strict-TypeScript browser client for playback and the review interaction
- FSRS 6 through the maintained Python implementation
- SQLite in WAL mode for the initial single-user deployment
- Mutagen and FFmpeg/ffprobe for metadata or audio analysis where browser-native behavior is insufficient
- `uv` for Python dependency management
- Docker/Compose for reproducible development and later private deployment

Do not replace this with a JavaScript full-stack framework, a separate API service, PostgreSQL, Redis, Celery, Kubernetes, or a native mobile app unless an accepted architecture decision explains why the existing design cannot meet a verified requirement.

## Product invariants

- A recognition card represents a musical target such as a work or movement, not one fixed excerpt.
- Every normal review should select a fresh valid region of the recording.
- FSRS decides **when** a target is reviewed.
- A separate excerpt-challenge policy decides **how much audio** is played and how difficult the sampled region should be.
- Typed answers are the learning task. Rating buttons are allowed only after the answer is submitted/revealed and are not multiple-choice answers.
- Answer acceptance must be deterministic and explainable. Prefer canonical answers plus user-managed aliases and documented normalization; do not use an LLM as the correctness judge.
- Review history must be append-only from the application perspective. Corrections should be explicit and auditable.
- Dates stored for scheduling are UTC-aware.
- The user must be able to export the durable learning data independently of the original audio files.

## Audio and media rules

- Never commit personal recordings, commercial recordings, extracted album art, or derived clips from user media.
- Generate synthetic test audio during tests or from a checked-in generation script.
- Do not reveal filenames, tags, paths, or embedded metadata on the question side of a review.
- Reject unsupported or malformed uploads safely and enforce size limits at both proxy and application layers.
- Preserve original files unless a separately documented migration explicitly replaces them.
- Prefer range-capable protected delivery and browser seeking for the MVP; introduce server-side transcoding only after compatibility tests justify it.

## Security and privacy

The application repository is public, but the intended deployment is private.

- Never commit `.env` files, Django secrets, credentials, private hostnames beyond the approved canonical hostname, user databases, review exports, backup configuration, or operational logs.
- Keep registration closed. The first deployment is single-user but data should remain user-scoped where doing so does not add disproportionate complexity.
- Do not add a public DNS/proxy route or assume public exposure is acceptable.
- Production access is intended through `repertory.metrekare.cloud` on LAN and approved WireGuard paths through the private ingress.
- Raw backend ports must not become a substitute access path.

## Development workflow

- Planning work may update documentation only unless implementation is explicitly authorized.
- Use a focused branch and pull request for nontrivial changes.
- Keep commits small enough to review and roll back.
- Add or update tests with every behavior change.
- Before requesting review, run the repository's formatting, linting, type, unit, integration, and browser tests that are relevant to the change.
- Do not deploy, restart homelab services, change DNS, edit Traefik, mount storage, or start/stop production containers from this repository task unless a separate HomelabTrack phase explicitly authorizes the exact live mutation.

## Definition of done for implementation work

A feature is not complete until:

- behavior and edge cases are documented;
- unit tests cover domain logic;
- browser/integration tests cover the user-visible path where applicable;
- accessibility and mobile behavior are checked;
- migrations and rollback are considered;
- no user media or secret data appears in the diff, test output, screenshots, or logs;
- the implementation plan and issue acceptance criteria are updated with evidence.