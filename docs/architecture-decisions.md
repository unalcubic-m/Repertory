# Initial architecture decisions

This document records the decisions to use when producing the first implementation plan. It is not live-deployment authorization.

## Decision summary

| Area | Initial decision |
| --- | --- |
| Product shape | Single-owner, web-first, installable PWA |
| Canonical application URL | Exact Render-provided HTTPS hostname; optional explicit custom domain later |
| Exposure | Public-network web endpoint with closed registration and authenticated application/media access |
| Backend | Python 3.13 with Django 5.2 LTS |
| Frontend | Django templates plus a small strict-TypeScript review/audio client |
| API style | Same-origin application endpoints; no separate public API service |
| Scheduler | FSRS 6 through `py-fsrs`, wrapped behind an application-owned interface |
| Initial database | SQLite with WAL mode and explicit backup/restore procedures |
| Media | Original user files on persistent storage; browser range playback first; FFmpeg fallback only if required |
| Runtime | One application container, no Redis/Celery/background worker in the MVP |
| Packaging | `uv`, Docker, and a Render Blueprint |
| Production ingress | Render-managed HTTPS edge and Docker web service |
| Sleep mode | No application-owned wake controller; follow the selected Render plan's lifecycle |

## 1. Use a dedicated Render origin, not a path prefix

The initial browser-facing URL is the exact `https://…onrender.com` hostname assigned to the web
service. Django reads it from Render's `RENDER_EXTERNAL_HOSTNAME`; the repository does not guess or
hard-code the generated name. An optional custom domain can be added later only after its exact hostname
is added to `REPERTORY_ALLOWED_HOSTS`.

A dedicated origin avoids Django script-prefix, static/media URL, CSRF-origin, cookie-path, PWA scope,
and proxy-rewrite complexity. Wildcard hosts and wildcard CSRF origins are not accepted.

## 2. Use Django as a small monolith

### Selected stack

- Python 3.13
- Django 5.2 LTS
- Django templates for library, settings, import, and statistics pages
- A focused TypeScript module for the review state machine, audio playback, timers, and keyboard behavior
- Ordinary same-origin HTML/JSON endpoints where each is the clearer interface

### Why

The application needs strong relational modeling, forms, authentication, file uploads, migrations, an administrative interface, deterministic scheduling logic, and only one highly interactive screen. A Django monolith satisfies these requirements without operating a separate frontend server or API service.

Django 5.2 is chosen over the newest non-LTS release to favor a longer support window and predictable dependency compatibility. Python also provides a maintained FSRS implementation and mature audio metadata tooling.

### Explicitly deferred

- Next.js, React, Vue, or a full single-page application
- FastAPI as a separate service
- GraphQL
- microservices
- native Android/iOS clients

These can be reconsidered only when a measured limitation cannot be addressed within the selected architecture.

## 3. Keep browser code small but typed

The review screen needs more than progressive HTML alone: precise playback start/stop behavior, a replay counter, duration timing, answer submission state, keyboard safety, and recovery from network or sleep transitions.

Use strict TypeScript compiled to static assets. Keep server state authoritative. The browser may hold the current review token and presentation state, but it must not be able to invent a valid review result, choose a different target after answer reveal, or submit the same review twice.

Do not put canonical answers or identifying recording metadata into the pre-answer HTML or JavaScript payload when avoidable.

## 4. Separate the scheduler from excerpt difficulty

Create two domain services with separate persisted state:

1. **Scheduling service**
   - Wraps FSRS 6.
   - Determines due dates and memory state from user ratings.
   - Stores enough immutable review history to replay/audit transitions.

2. **Challenge service**
   - Selects a duration band and permitted excerpt region.
   - Changes challenge level from explicit recorded inputs such as prior level, rating, match result, replays, and recent success.
   - Never rewrites FSRS parameters to make an audio question shorter.

This separation is a core correctness boundary and should have independent unit tests.

## 5. Use SQLite first

Use one SQLite database on local persistent storage with:

- WAL mode;
- a configured busy timeout;
- short transactions;
- one modest web-worker configuration until concurrency tests justify more;
- application-aware backup using SQLite's supported backup mechanism or a quiesced copy;
- integrity verification and an isolated restore test.

This is appropriate for the initial single-user, low-concurrency application and allows the full workload to stop without leaving a separate database service running. The Django ORM and migrations must remain portable enough for a later PostgreSQL migration if actual concurrency or operational evidence requires it.

Do not place the active SQLite database on NFS or an unverified network filesystem.

## 6. Store original audio outside Git

### Persistent data classes

- SQLite database and application metadata
- original audio assets
- optional generated analysis metadata such as permitted regions or waveform summaries
- application exports

Keep these in explicit persistent paths or volumes. Audio filenames on disk should be opaque identifiers rather than answer-bearing titles. Store the original user-visible filename only as protected metadata if it is needed for management.

### Import pipeline

1. Stream upload to a temporary location with bounded size.
2. Validate detected media type and decodability.
3. Compute a checksum and reliable duration.
4. Read tags as suggestions only.
5. Move the file atomically into governed storage.
6. Commit the corresponding database transaction or clean up on failure.

Use Mutagen for tag-level metadata and ffprobe/FFmpeg only where it adds verified value.

## 7. Prefer protected range playback for the MVP

The first implementation should test authenticated HTTP byte-range delivery and browser seeking on supported Android and desktop browsers.

A review request should create a server-side review session containing the selected target, asset, start time, duration, expiry, and one-time submission state. The browser receives only what it needs to request and play that range.

The TypeScript client should seek to the assigned start, play for the assigned duration, and stop precisely. The server remains authoritative about the assigned excerpt.

If variable-bitrate MP3 behavior or a supported browser makes seeking unreliable, add a bounded FFmpeg endpoint that produces a temporary/transient excerpt response. Do not pre-generate and retain a combinatorial library of random clips.

## 8. Use native Django authentication

The single-owner MVP uses Django authentication with:

- closed registration;
- one explicitly bootstrapped owner account;
- secure session cookies under HTTPS;
- CSRF protection;
- login throttling or an ingress/application equivalent selected during implementation planning;
- no anonymous media endpoints.

Do not depend on a separate identity provider for the initial deployment. Because the Render endpoint is
internet reachable, use a strong unique owner password, keep registration absent, and preserve
authenticated media endpoints, HTTPS-only cookies, CSRF protection, and exact host validation.

## 9. Render deployment model

The first hosted placement is one Render Docker web service in Frankfurt on the Starter plan, declared
by `render.yaml` and linked to the exact MVP branch. The request path is:

```text
Browser -> Render-managed HTTPS edge -> one Gunicorn worker -> Django
```

SQLite, original uploads, and sanitized playback files share one 5 GB persistent disk mounted at
`/var/lib/repertory`. Render's filesystem outside that mount is ephemeral. The disk restricts the
service to one instance and disables zero-downtime deploys, which is acceptable for a single-user MVP.
Migrations run in the runtime start command because Render pre-deploy commands cannot access attached
disks.

Deployment rules:

- Use the repository Dockerfile and Blueprint; deploy only a reviewed commit whose CI passed.
- Keep one Gunicorn worker while SQLite is the database.
- Generate `DJANGO_SECRET_KEY` in Render and keep all secrets and user data out of Git.
- Use WhiteNoise for immutable static assets; never use it or a public bucket for uploaded audio.
- Bootstrap one owner through a Render Shell and keep registration closed.
- Require readiness, login, upload, study, authenticated-range, persistence, restart, and anonymous-denial checks.
- Treat Render disk snapshots as recovery points, not a substitute for a tested SQLite/media backup.

## 10. Do not add an application wake controller

The Starter service is deployed normally. Repertory does not install Sablier, a Docker socket proxy, or
any application-owned scale-to-zero machinery on Render. If a future plan introduces platform sleep,
measure cold-start and active-review behavior before accepting it; do not build privileged lifecycle
automation into this app.

## 11. Testing strategy

The implementation plan should define at least:

- pure unit tests for answer normalization, FSRS adapter behavior, challenge transitions, excerpt selection, and time handling;
- Django model and constraint tests;
- file-import failure/cleanup tests;
- range and authorization tests;
- tests that identifying metadata is absent before answer reveal;
- concurrent/double-submit review tests;
- generated synthetic audio tests for duration, seeking, silence, and short-file behavior;
- browser tests on a desktop engine and Android-representative Chromium behavior;
- PWA cache tests proving private audio and authenticated pages are not retained unintentionally;
- backup/export/import and isolated restore tests;
- later wake/sleep integration tests if scale-to-zero is enabled.

## 12. Deployment and operational separation

Application code and the credential-free Render Blueprint live in this repository. Secrets, owner
credentials, uploaded audio, SQLite data, snapshots, runtime logs, and live deployment evidence remain
in Render or an approved private backup location. A code change does not itself authorize creating,
resizing, deleting, or restoring billable Render resources.

## Open decisions for the implementation plan

The planning phase must explicitly resolve:

- the exact explicit relational model for works, collections, movements, recordings, and targets;
- how one audio file maps to a full work versus individual movements;
- the review-session/token model and duplicate-submission protection;
- the exact answer-normalization rules and alias-conflict behavior;
- the initial challenge transition table and configuration surface;
- the supported MP3 limits and range-delivery implementation;
- how unusable regions are entered, detected, and edited;
- whether Django admin is sufficient for initial library management or a dedicated UI is required immediately;
- the exact PWA caching policy;
- export schema/versioning;
- dependency pinning and supply-chain checks;
- the initial worker/server choice and SQLite-safe concurrency settings;
- production storage sizing and whether original audio is included in every backup tier;
- the measured behavior of any future platform sleep policy.
