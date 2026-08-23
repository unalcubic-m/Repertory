# Codex planning prompt

> Superseded on 2026-08-23. The original private-homelab deployment assumptions below are retained only
> as the input that produced the initial plan; the current target is the Render deployment recorded in
> [`architecture-decisions.md`](architecture-decisions.md). Do not execute this prompt as current policy.

Use the prompt below from the Repertory repository root.

---

You are the planning agent for `unalcubic-m/Repertory`.

Your task is to produce a complete, implementation-ready plan for Repertory, a private web application that trains recognition of classical-music works and movements from changing user-supplied audio excerpts. This is a **planning and documentation task only**. Do not scaffold the Django project, add migrations, implement endpoints, build containers, change HomelabTrack or homelab infrastructure, or deploy anything.

## Repository and product context

Read these files in full before doing anything else:

1. `README.md`
2. `AGENTS.md`
3. `docs/product-brief.md`
4. `docs/architecture-decisions.md`
5. `docs/roadmap.md`

Then inspect the complete repository tree, current branch, recent commits, open issues, pull requests, and any existing planning files. Do not assume a referenced file exists without checking it. When documents conflict, identify the conflict explicitly instead of silently selecting one interpretation.

The key product loop is:

1. The user supplies an MP3/recording and metadata.
2. A due recognition target is selected.
3. The app plays a newly randomized excerpt without revealing identifying metadata.
4. The user types the work or movement title; this is free recall, not multiple choice.
5. The app reveals the canonical answer and the user rates Again/Hard/Good/Easy.
6. FSRS schedules the next review.
7. A separate challenge policy makes future excerpts shorter, easier, or harder based on performance.

A card represents a work or movement to recognize, **not one fixed audio clip**.

Maintain this strict separation:

- **FSRS determines when a recognition target is reviewed.**
- **The excerpt-challenge policy determines how difficult that review sounds.**

Do not manipulate FSRS intervals merely to make excerpts shorter or longer.

## Canonical URL and privacy invariant

The one and only approved browser-facing production URL is:

```text
https://repertory.metrekare.cloud
```

Treat this as a fixed project decision.

- Do not propose another subdomain.
- Do not propose mounting the application under a path prefix.
- Do not create or assume a public application route.
- The URL is privately resolved and reachable only from the home LAN and explicitly approved WireGuard clients through the existing private Traefik ingress.
- Native Django authentication remains required even on the private network.
- Use `repertory.metrekare.cloud` where a hostname is technically required, such as Django `ALLOWED_HOSTS`, DNS, TLS SNI, or a Traefik Host rule.
- Use `https://repertory.metrekare.cloud` where an origin or browser-facing URL is required, including Django `CSRF_TRUSTED_ORIGINS`, documentation, tests, PWA configuration, and examples.
- PWA `start_url` and service-worker scope should be designed for `/` on this dedicated origin, not for a subpath deployment.
- All newly produced documentation must use this exact canonical URL consistently.

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
- Canonical production URL `https://repertory.metrekare.cloud`.
- Private access only through LAN and approved WireGuard clients via the existing private Traefik ingress.
- Closed registration and native Django authentication.
- No public application route, public registration, Redis, Celery, separate API service, Kubernetes, or native mobile app in the MVP.
- Scale-to-zero is optional and later; the normal always-running deployment must work, be measured, and be accepted first.

## Research requirements

Use current official or primary sources for decisions that depend on framework, package, browser, database, FFmpeg, PWA, Docker, Traefik, Sablier, or security behavior. Prefer:

- official Django documentation and release/support information;
- the official Open Spaced Repetition/`py-fsrs` repository and documentation;
- Python, SQLite, FFmpeg, browser/MDN, Docker, Traefik, and Sablier documentation;
- standards or upstream project documentation rather than blog summaries.

Record links and the date checked in the resulting planning documents. Do not copy large passages. Clearly distinguish verified facts, selected decisions, assumptions, and experiments still required. State uncertainty where device or browser behavior still requires an experiment.

## Required planning work

### 1. Reconcile and refine the requirements

Create a requirement matrix mapping every MVP requirement and important edge case from `docs/product-brief.md` to:

- proposed component or module;
- persistence involved;
- security and privacy concern;
- required test level;
- delivery phase;
- acceptance evidence.

Identify contradictions, missing decisions, and scope that should be postponed. Do not silently expand the MVP.

### 2. Design the explicit relational data model

Compare at least two reasonable schemas, then select one. The chosen model must handle:

- composers and composer aliases;
- parent collections and child works, including *The Four Seasons* → *Spring* → movements;
- movements and their ordering and tempo labels;
- recordings independently from musical works;
- an audio file containing one movement, one complete work, or several movements;
- multiple recordings for one recognition target;
- work-level and movement-level recognition targets;
- canonical answers and explicit user-managed aliases;
- per-user scheduler state;
- per-user challenge state;
- append-only review logs;
- archive and deletion semantics;
- checksums, duration, permitted regions, unusable regions, and missing-media state;
- a future PostgreSQL migration without adopting an unnecessarily generic schema now.

For every model or table specify:

- fields and types;
- nullability;
- unique and check constraints;
- indexes;
- user ownership;
- lifecycle;
- archive and deletion behavior;
- backup and restore expectations.

Include a Mermaid entity-relationship diagram and representative worked examples for:

- Vivaldi's *The Four Seasons*;
- Bach's *Brandenburg Concerto No. 3*;
- a recording containing several movements.

### 3. Specify the review state machine

Define the server-authoritative lifecycle from requesting the next review through playback, typed-answer submission, answer reveal, rating, scheduler transition, challenge transition, completion, and immediate accidental-rating undo.

Resolve:

- one-time review tokens or session rows;
- expiration;
- refresh and reconnect behavior;
- two tabs and duplicate submissions;
- when the excerpt tuple becomes immutable;
- what information is safe to send before answer reveal;
- replay and hint tracking;
- immediate rating undo;
- transaction boundaries between review log, FSRS state, and challenge state;
- UTC and timezone handling;
- idempotency and audit requirements.

Include sequence diagrams for:

- a normal review;
- duplicate answer or rating submission;
- an expired review;
- refresh during a review;
- the first request after the application wakes from sleep.

### 4. Define deterministic answer matching

Specify exact normalization rules for:

- Unicode;
- case folding;
- whitespace;
- punctuation;
- apostrophes and hyphens;
- Roman and Arabic numerals;
- opus and catalogue numbers;
- localized titles;
- composer inclusion or exclusion.

The MVP judge must match only:

- the canonical answer;
- explicit user-managed aliases.

Do not use an LLM, embeddings, or unexplained fuzzy matching as the correctness judge. A conservative edit-distance result may be displayed only as an after-submission suggestion, with documented false-positive controls.

Define:

- alias uniqueness and conflict behavior;
- how the matched alias is shown;
- how a rejected answer can be promoted to a new alias after reveal;
- audit behavior for alias changes.

### 5. Design the FSRS integration

Use FSRS 6 but isolate it behind a Repertory-owned interface. Decide:

- whether FSRS objects are normalized into columns, stored as versioned JSON, or both;
- persisted FSRS state;
- how library upgrades and scheduler-version migrations are handled;
- what immutable review data is required to rebuild state;
- desired retention and learning/relearning defaults for the MVP;
- UTC-aware timestamps;
- previewing next intervals;
- accidental-rating undo and rollback;
- deterministic tests using fixed timestamps;
- why automatic parameter optimization is deferred;
- what amount and quality of review history would justify optimization later.

Do not invent performance or learning claims.

### 6. Design the independent excerpt-challenge policy

Create an explainable first policy using configurable duration bands and challenge levels. Define:

- initial challenge level;
- minimum and maximum durations;
- Again, Hard, Good, and Easy transitions;
- lapse behavior;
- replay and hint recording;
- evidence required before increasing difficulty;
- caps and anti-oscillation behavior;
- short-recording fallback;
- random duration selection inside a band;
- random permitted-region selection;
- recent-region avoidance;
- seeded randomness for tests.

Include:

- a complete transition table;
- worked success and lapse examples;
- tests proving that FSRS scheduling and challenge difficulty remain independent.

FSRS due intervals must not be changed merely to alter clip duration.

### 7. Design audio import and storage

Produce a threat-aware and failure-safe design for:

- upload size limits at ingress and Django layers;
- temporary staging;
- safe filename handling;
- extension, MIME, file-signature, decodability, and duration validation;
- checksums;
- duplicate-file behavior;
- tag extraction as untrusted suggestions;
- opaque persistent filenames;
- atomic database and file lifecycle;
- interrupted-upload cleanup;
- orphan cleanup;
- original-file preservation;
- missing or corrupt media;
- permitted and excluded regions;
- silence, applause, announcements, and tuning;
- synthetic audio generation for tests.

Personal recordings and derived clips must never enter Git, CI artifacts, screenshots, logs, or issue text.

### 8. Design playback architecture

Define a browser compatibility experiment before committing to the final playback implementation.

Test authenticated HTTP range delivery and seeking for supported MP3 files on:

- desktop Chromium;
- Android Chromium;
- any additional explicitly supported browser.

Resolve:

- variable-bitrate MP3 behavior;
- accurate randomized seeking;
- exact client-side stop timing;
- navigation and playback cleanup;
- preventing identifying metadata from appearing before reveal;
- authorization of range requests;
- expired-review access;
- whether a bounded FFmpeg excerpt endpoint is required.

If proposing an FFmpeg fallback, define:

- safe argument construction;
- CPU, memory, time, and output limits;
- concurrency limits;
- temporary-file cleanup;
- caching or no-caching decision;
- failure and timeout behavior.

Do not pre-generate a permanent library of random clips.

### 9. Design the web and PWA experience

Specify all planned routes and pages, including:

- login and account settings;
- library;
- work, movement, and recording management;
- audio import;
- due queue;
- review;
- answer reveal;
- progress;
- export and import;
- application settings.

Define the browser review state machine and cover:

- Android-first responsive layout;
- desktop behavior;
- keyboard and Enter-key safety;
- focus management;
- play and replay controls;
- audio stopping on navigation;
- network interruption;
- application wake state;
- accessibility and semantic controls;
- reduced motion;
- manifest and installability;
- explicit offline behavior;
- service-worker scope;
- exact cache allow and deny lists.

The PWA must use the dedicated origin `https://repertory.metrekare.cloud` with root scope. Do not design around a path-prefix deployment. Do not cache authenticated HTML, private audio, answers, or review state indiscriminately.

Evaluate whether ordinary Django forms plus the focused TypeScript client are sufficient. Add HTMX or another browser library only when a concrete interaction justifies it.

### 10. Define security and privacy controls

Threat-model at least:

- malicious or oversized media uploads;
- unsafe filenames and path traversal;
- metadata leakage;
- unauthorized media-range access;
- CSRF;
- session theft;
- login brute force;
- XSS through titles, notes, and aliases;
- duplicate or replayed review submissions;
- FFmpeg resource exhaustion;
- service-worker caching;
- backup and export leakage;
- public repository leakage;
- raw backend exposure;
- spoofed proxy headers;
- missing-media behavior;
- later wake-controller and Docker-socket compromise.

Define secure defaults, limits, logging redaction, secrets handling, and required tests. Registration remains closed. Network location alone must not replace native authentication.

The security model must assume:

```text
LAN or approved WireGuard client
  -> private split DNS for repertory.metrekare.cloud
  -> private Traefik
  -> guarded Repertory backend
```

The browser-facing origin must remain exactly `https://repertory.metrekare.cloud`. Public Internet, unknown WireGuard peers, undefined hosts, and direct raw-backend paths must fail closed.

### 11. Define development, CI, and test architecture

Specify the exact proposed project tree and module boundaries without creating them. Include:

- Django settings layout;
- domain and service modules;
- TypeScript structure;
- static-asset pipeline;
- dependency pinning;
- `uv.lock`;
- formatting;
- linting;
- type checking;
- unit tests;
- model and constraint tests;
- integration tests;
- browser tests;
- security tests;
- migration tests;
- export and import tests;
- isolated restore tests;
- performance and startup measurements;
- generated audio fixtures;
- GitHub Actions jobs;
- least-required Actions permissions;
- artifact retention rules;
- dependency review, SBOM, and image-scanning decisions;
- local commands that a clean checkout will run.

Every implementation milestone must name the tests that prove it.

### 12. Define production application compatibility without deploying

Document the application-side contract required by the later HomelabTrack deployment. Do not change HomelabTrack or any live system during this task.

Cover:

- the canonical application URL `https://repertory.metrekare.cloud`;
- Django `ALLOWED_HOSTS` containing `repertory.metrekare.cloud`;
- Django `CSRF_TRUSTED_ORIGINS` containing `https://repertory.metrekare.cloud`;
- container port;
- non-root runtime;
- health/liveness endpoint;
- readiness endpoint;
- persistent SQLite path;
- persistent media path;
- temporary-work path;
- environment variables;
- secret boundaries;
- secure cookies;
- proxy-header trust;
- upload limits;
- logging;
- graceful shutdown;
- database migrations;
- backup and quiescence commands;
- export and restore commands;
- resource limits;
- measurable cold-start behavior;
- no-public-route assumption.

The intended production path is:

```text
LAN or approved WireGuard client
  -> private split DNS for repertory.metrekare.cloud
  -> existing private Traefik ingress
  -> guarded Repertory backend
```

For optional scale-to-zero, compare always-running deployment with a Sablier-style on-demand start. Define the minimum evidence needed to choose:

- **Adopt**;
- **Defer**;
- **Reject**.

When describing the optional design, include:

- private Traefik wake middleware;
- pinned wake-controller version;
- least-privilege Docker socket proxy;
- controller restricted to the named Repertory workload;
- source-restricted controller API;
- health-gated wake;
- bounded startup timeout;
- private waiting or blocking-page behavior;
- active-review keepalive;
- inhibition during upload, migration, backup, restore, export, and maintenance;
- simultaneous first requests;
- stale browser tabs;
- failed startup;
- readiness timeout;
- controller outage;
- Docker API denial;
- rollback to always-running mode.

Treat any Traefik plugin or static-configuration change as a separate shared-ingress risk. Do not deploy it during this planning task.

### 13. Produce an ordered implementation backlog

Break the work into small, independently reviewable issues or milestones. For each item include:

- title;
- objective;
- dependencies;
- in scope;
- out of scope;
- exact files or modules expected to change;
- migration and data implications;
- required tests;
- acceptance criteria;
- rollback or rework boundary;
- risks;
- unresolved operator input.

The first implementation item after planning must create only the project skeleton and quality gates. It must not attempt the complete MVP.

## Required repository outputs

Create or update planning and documentation files only. At minimum produce:

- `docs/implementation-plan.md`
- `docs/data-model.md`
- `docs/review-and-audio-design.md`
- `docs/test-strategy.md`
- `docs/security-model.md`
- `docs/deployment-contract.md`
- `docs/implementation-backlog.md`
- relevant ADRs under `docs/adr/`

Update `README.md`, `docs/product-brief.md`, `docs/architecture-decisions.md`, and `docs/roadmap.md` only where reconciliation requires it. Preserve user intent and explain every changed decision.

Use diagrams where they add clarity. Keep commands illustrative and non-secret. Do not add fake test results or claim an unrun experiment passed.

## Quality bar

The plan must be detailed enough that a later Codex implementation task can take one backlog item at a time without inventing architecture. It must distinguish verified facts, selected decisions, experiments still required, and future or non-MVP ideas.

Before finishing:

1. Check every requirement and edge case from the product brief against the requirement matrix.
2. Check that FSRS and excerpt challenge remain separate.
3. Check that no pre-answer response leaks identifying information or the answer.
4. Check that every persistent object has lifecycle, constraints, archive/deletion behavior, backup ownership, and restore expectations.
5. Check that every milestone has tests and acceptance criteria.
6. Check that every browser-facing URL is exactly `https://repertory.metrekare.cloud`.
7. Check that no path-prefix URL, alternative subdomain, public exposure, or live deployment was introduced.
8. Run documentation, link, and lint checks that already exist; do not create feature code merely to satisfy a missing tool.
9. Do not claim unrun tests or experiments passed.

## Git workflow

- Work on a focused branch such as `codex/implementation-plan`.
- Commit only the planning documentation with a clear message.
- Push the branch.
- Open a pull request against `main` summarizing selected decisions, experiments still required, unresolved questions, and generated planning files.
- Do not merge the pull request.
- Do not begin implementation.

Return the pull-request URL and a concise list of the most important decisions, experiments, or unresolved blockers.

---
