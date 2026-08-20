# Initial architecture decisions

This document records the decisions to use when producing the first implementation plan. It is not live-deployment authorization.

## Decision summary

| Area | Initial decision |
| --- | --- |
| Product shape | Private, web-first, installable PWA |
| Canonical hostname | `repertory.metrekare.cloud` |
| Exposure | LAN and approved WireGuard only; no public application route |
| Backend | Python 3.13 with Django 5.2 LTS |
| Frontend | Django templates plus a small strict-TypeScript review/audio client |
| API style | Same-origin application endpoints; no separate public API service |
| Scheduler | FSRS 6 through `py-fsrs`, wrapped behind an application-owned interface |
| Initial database | SQLite with WAL mode and explicit backup/restore procedures |
| Media | Original user files on persistent storage; browser range playback first; FFmpeg fallback only if required |
| Runtime | One application container, no Redis/Celery/background worker in the MVP |
| Packaging | `uv`, Docker, and Docker Compose |
| Production ingress | Existing private Traefik file-provider architecture |
| Sleep mode | Design-compatible from the start; enable only after warm deployment is measured and accepted |

## 1. Use a subdomain, not a path prefix

Use:

```text
https://repertory.metrekare.cloud
```

Do not initially mount the application below `https://metrekare.cloud/repertory/`.

A dedicated hostname avoids permanent complexity around Django script prefixes, static/media URLs, CSRF origins, cookie paths, PWA manifest scope, service-worker scope, proxy rewrites, and wake-on-demand middleware. The hostname can still remain entirely private through split DNS.

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

The private MVP uses Django authentication with:

- closed registration;
- one explicitly bootstrapped owner account;
- secure session cookies under HTTPS;
- CSRF protection;
- login throttling or an ingress/application equivalent selected during implementation planning;
- no anonymous media endpoints.

Do not depend on Authelia for the initial private route. Native application authentication remains useful inside a private network and avoids coupling the development environment to homelab identity infrastructure. Public Authelia exposure is not an initial goal.

## 9. Private deployment model

Candidate production placement is DockerCoreVM, subject to a fresh capacity and storage preflight.

Intended request path:

```text
LAN or approved WireGuard client
  -> private split DNS for repertory.metrekare.cloud
  -> private Traefik on UbuntuServer / private VIP
  -> guarded Repertory backend on DockerCoreVM
```

Deployment rules:

- Add one exact private DNS record; do not rely on a new private wildcard.
- Publish no AAAA record unless an independently reviewed IPv6 path exists.
- Add no public VPS Caddy application handler.
- Keep the raw backend bound to the intended DockerCoreVM interface and allow only the private ingress source at the host firewall boundary.
- Use a pinned image/release and repository-driven Compose deployment.
- Keep secrets and user data out of Git.
- Require health, persistence, backup, restore, rollback, LAN, WireGuard, and public-fail-closed tests before acceptance.

The homelab repository, not this application repository, owns DNS, Traefik, firewall, storage attachment, backup scheduling, monitoring, and live deployment evidence.

## 10. Scale-to-zero is feasible but staged

The application is a good candidate for on-demand start because:

- review due dates are calculated when the user opens the app;
- no reminder daemon is required;
- SQLite and audio remain on persistent storage while the process is stopped;
- the first release intentionally avoids permanent background workers.

A suitable later design is Sablier or an equivalent reviewed wake controller:

```text
private Traefik middleware
  -> bounded Sablier API on DockerCoreVM
  -> least-privilege Docker socket proxy
  -> start Repertory container
  -> wait for /health/ready
  -> forward/retry the original request
```

After an inactivity window, the controller can stop the Repertory container and free its application memory. The first request after sleep either waits until health is ready or receives a private waiting page.

### Required safeguards

- Deploy and validate Repertory in normal always-running mode first.
- Measure idle memory, cold-start time, and operational value before accepting additional complexity.
- Treat the Traefik plugin/static-config change as a separate ingress mutation requiring review and restart planning.
- Never mount the unrestricted Docker socket directly into the wake controller; use a reviewed socket proxy with only the required container inspection/event/start/stop endpoints.
- Expose the wake-controller API only to the private ingress source.
- Require an application healthcheck that distinguishes process start from readiness.
- Use an inactivity period long enough for study sessions and uploads.
- Send a lightweight same-origin keepalive while an active review session is open, or otherwise prove the workload cannot stop mid-session.
- Inhibit scale-down during imports, migrations, backups, restores, and other critical operations.
- Prove that stale browser tabs, duplicate first requests, concurrent wake requests, container-start failure, and health timeout all fail safely.
- Provide a simple rollback to an always-running container without changing application data.

Scale-to-zero is not an MVP acceptance requirement. The application must be designed so it can be added without rewriting the product.

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

Application development proceeds in this repository. Live infrastructure work proceeds only through a HomelabTrack issue and the established approval gates.

Development completion does not authorize:

- creating DNS records;
- adding Traefik routers or plugins;
- changing firewalls;
- creating mounts/volumes on live hosts;
- pulling or starting production images;
- creating production credentials;
- enabling scale-to-zero;
- running backups/restores against production paths.

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
- the measured gate for adopting or rejecting scale-to-zero.