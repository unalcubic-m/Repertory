# Repertory delivery roadmap

This roadmap keeps application development, production deployment, and optional scale-to-zero as separate acceptance boundaries.

## Phase 0 — implementation planning

Deliverables:

- inspect the repository and confirm the product/architecture decisions;
- research current official documentation for selected dependencies;
- produce an explicit relational data model and lifecycle diagrams;
- define review-session, answer-matching, scheduling, challenge, media, export, and security contracts;
- choose exact dependency versions and lock strategy;
- define the test pyramid and generated-audio fixture strategy;
- break implementation into small issues or milestones with acceptance criteria;
- record unresolved decisions instead of hiding assumptions.

Gate: no feature code until the plan is internally consistent and accepted.

## Phase 1 — project skeleton and quality gates

Deliverables:

- Django project and application modules;
- strict settings split for development/test/production;
- `uv.lock` and reproducible dependency installation;
- TypeScript asset pipeline with strict type checking;
- formatting, linting, typing, unit-test, and browser-test entry points;
- GitHub Actions CI with least required permissions;
- health/live and health/ready endpoints with no sensitive detail;
- synthetic audio generation helper for tests;
- secure defaults for uploads, sessions, CSRF, headers, and logging.

Acceptance:

- clean checkout can be installed and tested from documented commands;
- CI passes;
- no production secret or user media is required for tests;
- container builds reproducibly and runs as a non-root user where practical.

## Phase 2 — repertoire domain and library management

Deliverables:

- composer, work/collection, movement, recording, audio asset, recognition target, and alias schema;
- database constraints and migrations;
- owner scoping;
- admin or dedicated management UI;
- archive semantics without review-history deletion;
- deterministic answer normalization and alias conflict handling;
- metadata import suggestions without silent trust.

Acceptance:

- representative classical structures, including *The Four Seasons* hierarchy, can be modeled without duplicate cards or misleading relationships;
- short aliases and localized titles work predictably;
- deletion/archive operations preserve or reject dependent data safely.

## Phase 3 — safe audio import and playback

Deliverables:

- bounded upload flow with temporary staging and cleanup;
- checksum, duration, format, and decodability validation;
- opaque persistent filenames;
- permitted/unusable region editing;
- authenticated range-capable playback endpoint;
- TypeScript playback controller with exact stop behavior and safe navigation cleanup;
- browser compatibility evidence on Android and desktop;
- documented FFmpeg fallback decision.

Acceptance:

- supported MP3 files import and play from randomized positions;
- identifying tags and filenames are absent on the question side;
- invalid/interrupted uploads leave no orphaned durable state;
- unsupported or too-short assets fail with a useful message.

## Phase 4 — review engine

Deliverables:

- due queue and review-session token model;
- one-time answer submission and one-time rating transition;
- FSRS 6 adapter and persisted scheduler state;
- append-only review logs;
- Again/Hard/Good/Easy flow;
- immediate accidental-rating undo;
- independent challenge state and transition table;
- random excerpt selector with recent-region avoidance;
- deterministic typed-answer matching and alias promotion after reveal.

Acceptance:

- end-to-end review works without multiple-choice answers;
- duplicate tabs/submissions cannot create two scheduler transitions;
- FSRS and challenge tests prove their independence;
- lapses make questions easier and sustained success can make them shorter;
- fresh excerpts are used across repeated reviews.

## Phase 5 — mobile UX, PWA, progress, and portability

Deliverables:

- responsive mobile-first review screen;
- accessible keyboard/focus behavior;
- PWA manifest and deliberately limited service worker;
- clear online/offline and waking states;
- due/new/learned/lapsed statistics;
- per-target progress details;
- versioned data export and import;
- documented backup/restore behavior for database and media.

Acceptance:

- a complete study session works from Android and desktop;
- private media/authenticated pages are not unintentionally cached;
- export/import preserves review history and scheduler state;
- an isolated restore succeeds.

## Phase 6 — development acceptance

Deliverables:

- seed or import at least twenty personally supplied recognition targets outside Git;
- sustained real-use test over enough reviews to expose queue and challenge problems;
- performance, memory, startup, storage, and upload measurements;
- security and dependency review;
- release notes and exact release/image provenance;
- production-readiness checklist and rollback contract.

Gate: application development is accepted before production infrastructure is changed.

## Phase 7 — private homelab deployment

Owned by HomelabTrack, not by an application-only task.

Deliverables:

- fresh Proxmox/DockerCore capacity and storage preflight;
- recovery point before mutation;
- governed persistent storage for database and audio;
- pinned Compose deployment on the approved target;
- raw-origin firewall restriction to the private ingress source;
- explicit private Traefik router for `repertory.metrekare.cloud`;
- exact private split-DNS record and no AAAA unless reviewed;
- no public VPS application route;
- owner bootstrap outside Git/logs;
- LAN and approved WireGuard acceptance;
- public fail-closed verification;
- backup, encrypted off-VM copy, missed-run visibility, and isolated restore;
- monitoring, upgrade, rollback, and repository synchronization.

Acceptance:

- the app is privately usable at the canonical hostname;
- raw backend and public paths remain unavailable;
- persistence, backup, restore, restart/recreate, and rollback are proven.

## Phase 8 — optional scale-to-zero evaluation

First measure the normal deployment. Record idle RSS, cold-start time, active-study behavior, backup interaction, and the resource benefit that stopping the app would provide.

Decision outcome must be one of:

- **Adopt** guarded scale-to-zero;
- **Defer** until a named condition;
- **Reject** because the operational/security cost exceeds the resource benefit.

If adopted, deliver:

- pinned wake-controller and Traefik middleware versions;
- least-privilege Docker socket proxy;
- source-restricted controller API;
- health-gated wake behavior;
- waiting/blocking cold-start UX;
- active-session keepalive or equivalent protection;
- scale-down inhibition for uploads, migrations, backup, restore, and maintenance;
- bounded idle timeout;
- concurrent wake, stale tab, startup failure, timeout, and mid-session tests;
- rollback to an always-running app.

Scale-to-zero is complete only after it survives ordinary use and a controlled host/container restart without exposing another Docker workload or weakening the private ingress.

## Future candidates after the first release

- prompt modes for composer, period, form, catalogue number, or movement;
- multiple recordings per target with performance randomization;
- user-defined learning collections/decks;
- better audio region analysis or waveform editing;
- personal FSRS parameter optimization after enough trustworthy history;
- optional offline review packs with explicit encrypted/device-local storage rules;
- sharing metadata-only repertoire packs without recordings;
- native application wrappers only if the PWA has a measured limitation.