# Codex planning prompt

Use the prompt below from the Repertory repository root.

---

You are the planning agent for `unalcubic-m/Repertory`.

Your task is to produce a complete, implementation-ready plan for Repertory, a private web application that trains recognition of classical-music works and movements from changing user-supplied audio excerpts. This is a **planning and documentation task only**. Do not scaffold the Django project, add migrations, implement endpoints, build containers, change homelab infrastructure, or deploy anything.

## Repository and product context

Read these files in full before doing anything else:

1. `README.md`
2. `AGENTS.md`
3. `docs/product-brief.md`
4. `docs/architecture-decisions.md`
5. `docs/roadmap.md`

Then inspect the complete repository tree, current branch, recent commits, open issues, and any existing planning files. Do not assume a referenced file exists without checking it.

The key product loop is:

1. The user supplies an MP3/recording and metadata.
2. A due recognition target is selected.
3. The app plays a newly randomized excerpt without revealing identifying metadata.
4. The user types the work or movement title; this is free recall, not multiple choice.
5. The app reveals the canonical answer and the user rates Again/Hard/Good/Easy.
6. FSRS schedules the next review.
7. A separate challenge policy makes future excerpts shorter/easier/harder based on performance.

A card represents a work or movement to recognize, **not one fixed audio clip**.

## Accepted starting decisions

Treat these as the starting architecture. Challenge one only when you can show a concrete requirement it cannot meet and record the alternative as an explicit ADR.

- Python 3.13.
- Django 5.2 LTS as a small monolith.
- Django templates for ordinary pages.
- A small strict-TypeScript client for review/audio behavior; no full SPA by default.
- FSRS 6 through the maintained Python implementation, behind an application-owned adapter.
- SQLite in WAL mode for the initial single-user deployment, with a clean future PostgreSQL migration path.
- Mutagen plus FFmpeg/ffprobe only where needed.
- Authenticated HTTP range delivery and browser seeking as the first audio strategy; bounded server-side FFmpeg excerpt generation only as a tested fallback.
- `uv` for Python dependency management.
- Docker/Compose for reproducible development and eventual deployment.
- Responsive installable PWA, online-first.
- Canonical production hostname `repertory.metrekare.cloud`.
- Private access only through LAN and approved WireGuard clients via the existing private Traefik ingress.
- No public application route, public registration, Redis, Celery, separate API service, Kubernetes, or native mobile app in the MVP.
- Scale-to-zero is optional and later; the warm deployment must work first.

## Research requirements

Use current official/primary sources for decisions that depend on framework, package, browser, database, FFmpeg, PWA, Docker, Traefik, Sablier, or security behavior. Prefer:

- official Django documentation and release/support information;
- the official Open Spaced Repetition/`py-fsrs` repository and documentation;
- Python, SQLite, FFmpeg, browser/MDN, Docker, Traefik, and Sablier documentation;
- standards or upstream project documentation rather than blog summaries.

Record links and the date checked in the resulting planning documents. Do not copy large passages. State uncertainty where device/browser behavior still requires an experiment.

## Required planning work

### 1. Reconcile and refine the requirements

Create a requirement matrix mapping every MVP requirement and important edge case from `docs/product-brief.md` to:

- proposed component/module;
- persistence involved;
- security/privacy concern;
- required test level;
- delivery phase;
- acceptance evidence.

Identify contradictions, missing decisions, and scope that should be postponed. Do not silently expand the MVP.

### 2. Design the explicit relational data model

Compare at least two reasonable schemas, then select one. The chosen model must handle:

- composers and aliases;
- parent collections and child works, including *The Four Seasons* → *Spring* → movements;
- movements and their ordering/tempo labels;
- recordings independent from works;
- an audio file containing one movement, one complete work, or several movements;
- multiple recordings for one recognition target;
- work-level and movement-level recognition targets;
- canonical answers and explicit user-managed aliases;
- per-user scheduler and challenge state;
- append-only review logs;
- archive/delete semantics;
- checksums, duration, permitted/unusable regions, and missing-media state;
- future migration without adopting an unnecessarily generic schema now.

For every model/table specify fields, types, nullability, unique/check constraints, indexes, ownership, lifecycle, and deletion behavior. Include a Mermaid ER diagram and representative examples for Vivaldi's *The Four Seasons*, Bach's *Brandenburg Concerto No. 3*, and a multi-movement recording.

### 3. Specify the review state machine

Define the server-authoritative lifecycle from “request next review” through playback, answer submission, reveal, rating, and completion. Resolve:

- one-time review tokens/session rows;
- expiration;
- refresh/reconnect behavior;
- two tabs and duplicate submissions;
- when the excerpt tuple becomes immutable;
- what data is safe to send before reveal;
- replay and hint tracking;
- immediate rating undo;
- transactional boundaries between review log, FSRS state, and challenge state;
- clock/timezone handling;
- idempotency and audit requirements.

Include sequence diagrams for a normal review, duplicate submission, expired session, and wake-from-sleep request.

### 4. Define deterministic answer matching

Specify exact Unicode normalization, case folding, punctuation, whitespace, numeral, opus/catalogue, and localized-title behavior. Explain how canonical answers and aliases are stored and compared, how conflicts are surfaced, and how a rejected answer can be promoted to an alias after reveal.

Do not use an LLM, embeddings, or unexplained fuzzy matching as the MVP judge. If a conservative edit-distance suggestion is proposed, keep it advisory and document false-positive controls.

### 5. Design the FSRS integration

Use FSRS 6 but isolate it behind a Repertory interface. Decide:

- whether FSRS objects are normalized into columns, stored as versioned JSON, or both;
- how library upgrades and scheduler-version migrations are handled;
- what immutable review data is required to rebuild state;
- desired retention and learning/relearning defaults for the MVP;
- UTC/time handling;
- previewing next intervals;
- undo/rollback;
- why automatic parameter optimization is deferred and what data threshold could enable it later.

Create tests using fixed timestamps and known transitions. Do not invent performance claims.

### 6. Design the independent excerpt-challenge policy

Create an explainable first policy using configurable duration bands and challenge levels. Define inputs, transitions, caps, lapse behavior, replay/hint effects, and how the policy avoids oscillation.

Separate:

- challenge-level selection;
- random duration selection inside a band;
- random permitted-region selection;
- recent-region avoidance;
- short-recording fallback;
- seeded randomness for tests.

Show a transition table and worked examples. FSRS due intervals must not be changed merely to alter clip duration.

### 7. Design audio import, storage, and playback

Produce a threat-aware and failure-safe design for:

- upload size limits at ingress and Django;
- temporary staging;
- extension, MIME, signature, decodability, and duration checks;
- checksum and deduplication policy;
- tag extraction as untrusted suggestions;
- opaque storage names;
- atomic database/file lifecycle and orphan cleanup;
- permitted/unusable regions and silence/applause handling;
- authenticated range requests;
- variable-bitrate MP3/browser seeking tests;
- exact stop timing in TypeScript;
- FFmpeg fallback criteria, command safety, resource/time limits, and caching decision;
- preventing filenames/tags/artwork from leaking before reveal;
- missing/corrupt media recovery;
- synthetic test-audio generation.

Define a small device/browser compatibility experiment before committing to the final playback implementation.

### 8. Design the web/PWA experience

Specify routes/pages and the review-page client state. Cover:

- desktop and Android mobile layout;
- keyboard/focus behavior;
- play/replay/submit/rate safety;
- accessibility;
- network interruption and application wake state;
- manifest and installability;
- service-worker scope and cache allow/deny list;
- explicit offline behavior;
- preventing private audio/authenticated HTML from being cached indiscriminately.

Decide whether ordinary pages need HTMX or whether normal Django forms plus the focused TypeScript review client are simpler. Do not add a frontend framework without evidence.

### 9. Define security and privacy controls

Threat-model at least:

- malicious/oversized media uploads;
- path traversal and unsafe filenames;
- metadata leakage;
- unauthorized media range access;
- CSRF/session theft;
- login brute force;
- XSS through user-entered metadata/aliases;
- duplicate/replayed review requests;
- public repository secret/media leakage;
- raw backend exposure;
- service-worker/browser caching;
- FFmpeg resource exhaustion;
- backup/export leakage;
- wake-controller/Docker-socket compromise in the later scale-to-zero phase.

Define secure defaults, logging redaction, limits, and tests. Keep registration closed.

### 10. Define development, CI, and test architecture

Specify the exact proposed project tree and module boundaries without creating them. Include:

- settings layout;
- domain/service modules;
- TypeScript structure;
- dependency and lock strategy;
- formatting/lint/type tools;
- unit, model, integration, browser, security, migration, export/restore, and performance tests;
- generated audio fixtures;
- GitHub Actions jobs, caching, artifact policy, and least permissions;
- dependency review/SBOM/image scanning decisions;
- local commands that a clean checkout will run.

Every implementation milestone must name the tests that prove it.

### 11. Define production compatibility without deploying

Document the application contract needed by the later HomelabTrack deployment:

- container ports and non-root runtime;
- health/live and health/ready semantics;
- persistent paths for database, media, and temporary work;
- environment variables and secret boundaries;
- proxy headers, allowed hosts, CSRF origins, secure cookies, upload limits, and logging;
- graceful shutdown and migration behavior;
- backup/quiescence/export/restore commands;
- resource limits and measurable cold-start behavior;
- no public route assumption.

For optional scale-to-zero, compare always-running versus Sablier-style on-demand start. Define the minimum evidence needed to Adopt, Defer, or Reject it. Include least-privilege Docker socket proxy, source-restricted Sablier API, Traefik plugin/static-config risk, health-gated wake, active-session keepalive, critical-operation inhibition, concurrent-wake tests, and rollback to always-running mode.

Do not edit HomelabTrack or any live system during this task.

### 12. Produce an ordered implementation backlog

Break the work into small, independently reviewable issues or milestones. For each item include:

- title and objective;
- dependencies;
- in-scope/out-of-scope;
- exact files/modules expected to change;
- migration/data implications;
- tests;
- acceptance criteria;
- rollback/rework boundary;
- risks and unresolved inputs.

The first issue after planning should create only the project skeleton and quality gates, not the entire MVP.

## Required repository outputs

Create or update only planning/documentation files. At minimum produce:

- `docs/implementation-plan.md`
- `docs/data-model.md`
- `docs/review-and-audio-design.md`
- `docs/test-strategy.md`
- `docs/security-model.md`
- `docs/deployment-contract.md`
- `docs/implementation-backlog.md`
- ADRs under `docs/adr/` for decisions that materially refine or change the accepted starting architecture

Update `README.md`, `docs/product-brief.md`, `docs/architecture-decisions.md`, and `docs/roadmap.md` only where reconciliation requires it. Preserve user intent and explain every changed decision.

Use diagrams where they add clarity. Keep commands illustrative and non-secret. Do not add fake test results or claim an unrun experiment passed.

## Quality bar

The plan must be detailed enough that a later Codex implementation task can take one backlog item at a time without inventing architecture. It must distinguish verified facts, chosen decisions, experiments still required, and future/non-MVP ideas.

Before finishing:

1. Check every requirement and edge case from the product brief against the requirement matrix.
2. Check that FSRS and excerpt challenge remain separate.
3. Check that no pre-answer response leaks the answer.
4. Check that every persistent object has lifecycle, constraints, backup, and deletion behavior.
5. Check that every milestone has tests and acceptance criteria.
6. Check that no public exposure or live deployment was authorized.
7. Run documentation/link/lint checks that already exist; do not create feature code merely to satisfy a missing tool.

## Git workflow

- Work on a focused branch such as `codex/implementation-plan`.
- Commit the documentation with a clear message.
- Push the branch.
- Open a pull request against `main` summarizing decisions, experiments, unresolved questions, and generated planning files.
- Do not merge the PR and do not begin implementation.

Return the pull-request URL and a concise list of the most important decisions or unresolved blockers.

---