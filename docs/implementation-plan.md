# Repertory implementation-planning documentation

## Summary

Extend the existing branch and PR [#1](https://github.com/unalcubic-m/Repertory/pull/1) with documentation only. Do not scaffold Django, create migrations, build containers, modify HomelabTrack, deploy, or merge the PR.

The planning baseline is the open PR because `main` currently contains only `README.md`; the required `AGENTS.md` and `docs/` inputs exist only on `agent/plan-repertory-architecture`. There are no open issues or other open PRs.

Reconciliation will explicitly record:

- `docs/roadmap.md` incorrectly postpones multiple recordings per target even though the product brief requires it in the MVP; move it into the MVP backlog.
- MP3 is the only MVP import format. Other formats remain post-MVP experiments.
- Dedicated owner-facing management pages are required; Django admin may assist operators but is not the sole library UI.
- Desktop Chromium and Android Chromium are the formal MVP browsers. Firefox and Safari remain best-effort and ungated.
- `https://repertory.metrekare.cloud` remains the only browser-facing production URL.

All research-dependent claims will cite upstream documentation and say “checked 2026-08-20.” Key sources include official [Django 5.2 documentation](https://docs.djangoproject.com/en/5.2/), [py-fsrs](https://github.com/open-spaced-repetition/py-fsrs), [SQLite WAL](https://www.sqlite.org/wal.html), [FFmpeg](https://ffmpeg.org/documentation.html), [MDN range requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Range_requests), [Docker](https://docs.docker.com/), [Traefik](https://doc.traefik.io/traefik/), and [Sablier](https://github.com/sablierapp/sablier).

## Documentation changes

- Create `docs/implementation-plan.md` with:
  - a requirement matrix containing every product-brief MVP bullet and edge case;
  - component, persistence, privacy risk, test level, delivery phase, and acceptance evidence columns;
  - verified facts, decisions, assumptions, experiments, and future ideas clearly labeled;
  - the exact proposed project tree and module boundaries.

- Create `docs/data-model.md` with:
  - comparison of a polymorphic/generic model against the selected explicit relational model;
  - complete field dictionaries, defaults, nullability, constraints, indexes, ownership, lifecycle, archive/deletion, backup, and restore policy;
  - a Mermaid ER diagram;
  - worked Vivaldi/Four Seasons, Brandenburg No. 3, complete multi-movement file, movement-only file, and multiple-performance examples.

- Create `docs/review-and-audio-design.md` with:
  - server and browser state machines;
  - deterministic answer matching;
  - FSRS adapter;
  - independent challenge policy;
  - import, protected range playback, and bounded FFmpeg fallback;
  - all requested Mermaid sequence diagrams.

- Create `docs/test-strategy.md`, `docs/security-model.md`, `docs/deployment-contract.md`, `docs/implementation-backlog.md`, and `docs/research-sources.md`.

- Add ADRs for:
  - explicit catalog/audio-coverage schema;
  - persisted review sessions and append-only transitions;
  - FSRS adapter and independent challenge state;
  - sanitized full-length playback media and range-first delivery;
  - root-scope online-first PWA caching;
  - deferring scale-to-zero pending measurements.

- Reconcile `README.md`, `docs/product-brief.md`, `docs/architecture-decisions.md`, and `docs/roadmap.md` only where needed, including links to the new documents and the multiple-recordings conflict.

## Selected technical specification

### Relational model

Use `BigAutoField` internal keys and UUID public identifiers. Store durations and media boundaries as non-negative integer milliseconds and all timestamps as UTC-aware datetimes.

The explicit model will contain:

- `Composer`, `ComposerAlias`, self-parented `Work` with `collection`/`work` kind, and ordered `Movement`.
- `Recording` for performance metadata, independent of files.
- `AudioAsset` for an immutable original file, owner-scoped unique SHA-256, opaque path, size, MIME/signature/probe results, duration, and ready/missing/corrupt/purged state.
- `PlaybackAsset` as a regenerable, full-length, metadata-free MP3 derivative. Only this derivative may be used pre-answer; original ID3 tags and artwork must never reach the review browser.
- `RecordingSource` linking recordings to assets, `AudioCoverage` mapping time spans explicitly to either one work or one movement, and permitted/excluded `AudioRegion` rows.
- `RecognitionTarget` with exactly one work or movement reference and one canonical answer.
- `TargetSource` explicitly enabling one or more coverage rows/performances for a target.
- `AnswerAlias` plus append-only `AnswerAliasAudit`.
- Per-user `SchedulerState`, `ChallengeState`, and versioned scheduler/challenge configurations.
- `ReviewSession`, append-only `ReviewSessionEvent`, immutable `ReviewLog`, and `ReviewUndoEvent`.
- `ImportAttempt` for recoverable staged imports.

Exactly-one work/movement checks, positive range checks, sequence uniqueness, owner-scoped checksum uniqueness, one scheduler/challenge state per user-target, one target per work/movement, one enabled target-source pairing, and one open review per user will be database constraints where portable. Cross-row bounds, hierarchy validity, overlap rules, and owner consistency will also be service validations and tests.

Library objects are archived rather than deleted. Historical rows use `PROTECT`; media purge retains an asset tombstone. Account deletion is outside the MVP and must not cascade silently. Database metadata and originals belong to backup/restore; playback derivatives and temporary files are reproducible and excluded from mandatory backup.

### Review and answer contract

Allow one persisted open review per user. A session has a two-hour absolute lifetime and freezes the target, source, asset, primary excerpt, optional longer-hint duration, challenge snapshot, and expiry before returning the question payload.

Use client-generated UUID idempotency keys and conditional state updates:

- Duplicate answer/rating requests with the same key and payload return the stored result.
- A reused key with different content, or a different operation after the transition, returns `409`.
- Rating applies the FSRS transition, challenge transition, scheduler/challenge state updates, immutable log, and session completion in one transaction.
- Scheduler failure rolls back the entire rating transaction and leaves the session reveal-ready.
- Refresh, reconnect, another tab, or application restart resumes the same persisted session and stage.
- Server UTC time is authoritative. A clock rollback behind the target’s last review fails safely without inventing a timestamp.
- Expired sessions cannot access audio or mutate scheduling.

Immediate undo is available for ten minutes and only while the log is the target’s latest effective rating. It appends an undo event, restores stored pre-transition scheduler/challenge snapshots, and returns the session to reveal-ready; re-rating creates a new immutable log.

Pre-answer responses contain only the session UUID, duration, generic playback URL, controls, and booleans such as hint availability. They exclude answers, aliases, target/recording metadata, filenames, paths, tags, artwork, and answer-bearing URLs.

Normalize answers with versioned Python 3.13 behavior:

1. Reject empty or over-256-character input.
2. Apply Unicode NFKC and convert Unicode decimal digits to ASCII.
3. Apply `casefold()`.
4. Remove quotation marks; remove apostrophes without splitting a word.
5. Convert hyphens, dashes, ordinary punctuation, and brackets to spaces.
6. Collapse Unicode whitespace and trim.
7. Split known catalogue prefixes (`BWV`, `K`, `RV`, `D`, `Op`, `No`) from adjacent digits and normalize their punctuation/spacing.

Do not convert Roman numerals to Arabic numerals, expand abbreviations, translate titles, infer nicknames/subtitles, or add/remove composer names. Those variants require explicit aliases. Match only the canonical normalized value or an active alias for that target. Identical values across different targets are allowed; duplicates within one target are rejected. No fuzzy acceptance or edit-distance suggestion ships in the MVP.

### FSRS and challenge independence

The application-owned scheduler interface will expose pure `initialize`, `preview`, `apply`, `serialize`, and `rebuild` operations. Persistence stores normalized card columns plus versioned py-fsrs-compatible JSON, configuration revision, algorithm version, package version, and immutable pre/post snapshots.

Use FSRS 6 defaults initially:

- desired retention `0.90`;
- learning steps `1m, 10m`;
- relearning step `10m`;
- maximum interval `36500` days;
- fuzzing disabled so rebuilds and fixed-time tests are deterministic.

Parameter optimization remains deferred. Evaluation becomes eligible—not automatically adopted—after at least 1,000 non-undone, valid, chronologically consistent reviews across at least 100 targets and 90 days, followed by an independently reviewed offline comparison.

Challenge levels use bands `30–45`, `22–32`, `15–24`, `10–16`, `7–11`, and `4–8` seconds. New targets start at level 0.

A clean success means Good/Easy, an accepted typed answer, no hint, and no replay:

- Again: decrease two levels, floor 0.
- Hard: decrease one level, floor 0.
- Good: add one clean-success credit.
- Easy: add two clean-success credits.
- Increase by at most one level only when credit is at least two and at least two reviews have occurred at the current level.
- Any decrease or non-clean result resets upward credit; every level change resets the level-review counter.

Duration is uniformly sampled within the band. Source and valid start selection use injected randomness, permitted regions minus exclusions, recent-source/region avoidance over five completed reviews, and deterministic seeds in tests. If the longest valid window is below the band minimum but at least four seconds, use that longest window and record a short-source fallback without altering challenge level. Sources with no four-second valid window are unavailable.

FSRS receives only the explicit rating and review timestamp. Challenge transitions never alter FSRS parameters or due intervals.

### Import, playback, web, and PWA

Set the default maximum upload to 512 MiB and maximum duration to six hours, enforced by Traefik buffering and a counting Django temporary-file upload handler. Accept `.mp3` only; client MIME is advisory, while libmagic/file signature, ffprobe structure/duration, Mutagen parsing, and bounded full audio decoding are authoritative.

Uploads use same-filesystem opaque staging, streaming SHA-256, persisted import attempts, atomic rename, compensating cleanup, and a stale-stage/orphan reconciliation command. Exact owner duplicates reuse the existing asset after confirmation rather than storing duplicate bytes.

The range endpoint serves only sanitized playback assets, supports authenticated single-byte ranges with correct `200`, `206`, and `416` behavior, uses opaque session URLs, and sends `Cache-Control: private, no-store, no-transform`.

Before finalizing range playback, run synthetic CBR and VBR MP3 experiments on current desktop Chromium and physical Android Chromium. Test start/middle/end seeking, insufficient buffering, replay, navigation, sleep/wake, and network interruption. Require start error no greater than 500 ms and stop overshoot no greater than 250 ms for every required fixture/device. Failure requires the documented FFmpeg fallback ADR.

The fallback uses argument arrays without a shell, local-file-only protocols, one audio stream, stripped metadata/artwork, a 15-second wall timeout, 10-second CPU limit, 256 MiB process memory ceiling, 16 MiB output ceiling, concurrency one, and guaranteed temporary cleanup. It returns a generic retryable error and never logs paths or metadata. Random clips are never permanently pre-generated or cached.

Use ordinary Django forms for management and a strict-TypeScript client only for review/audio/PWA behavior. Define dedicated routes for accounts, composers, works/collections, movements, recordings, import, regions, targets/aliases, due queue, active review, reveal/rating/undo, progress, export/import, settings, manifest, service worker, offline page, and health endpoints.

The PWA uses `start_url: "/"` and `scope: "/"` on `https://repertory.metrekare.cloud`. Its generated cache allow list contains only fingerprinted CSS/JS/icons/fonts, the manifest, and a generic offline page. It never caches navigation responses, authenticated HTML, audio/range requests, answers, aliases, review endpoints/state, exports, account data, health responses, POSTs, or responses marked private/no-store.

### Security, deployment, and scale-to-zero

Production settings hard-code:

- `ALLOWED_HOSTS = ["repertory.metrekare.cloud"]`;
- `CSRF_TRUSTED_ORIGINS = ["https://repertory.metrekare.cloud"]`;
- secure, HTTP-only, SameSite=Lax session cookies;
- secure CSRF cookies;
- no forwarded host trust;
- `SECURE_PROXY_SSL_HEADER` only when the backend is source-restricted to the sanitizing private Traefik hop.

Use closed registration, native Django authentication, database-backed django-axes throttling, normal template escaping, strict CSP/security headers, redacted structured logs, secret files, and fail-closed authorization for every media/review/data route.

The application contract uses port `8000`, UID/GID `10001`, a read-only root filesystem, `/var/lib/repertory/db/repertory.sqlite3`, `/var/lib/repertory/media`, and `/var/tmp/repertory`. SQLite WAL remains on local storage. `/health/live/` checks the process; `/health/ready/` checks database access, migration state, and required writable storage without exposing details. Migrations run as an explicit one-shot command, not during web startup.

Scale-to-zero is presently **Defer**. Document candidate pinned Sablier `1.16.1` and Traefik plugin `1.3.0`, with immutable image/plugin digests required before adoption, `failOpen=false`, named-workload authorization, a least-privilege socket proxy, source-restricted API, health-gated wake, and maintenance inhibition.

Adopt only after a 30-day always-running baseline shows operationally meaningful host pressure, at least 256 MiB reclaimable idle RSS, P95 readiness within 15 seconds and P99 within 30 seconds, successful concurrent-wake and active-operation tests, and reviewed Docker permissions. Reject if it requires unrestricted Docker access, fail-open routing, public controller exposure, unacceptable ingress risk, or P95 startup above 30 seconds. Otherwise continue to defer.

## Test, backlog, and delivery plan

`docs/test-strategy.md` will map every milestone to unit, model/constraint, integration, browser, security, migration, export/import, restore, performance, and startup tests. Synthetic WAV generation and FFmpeg CBR/VBR encoding use fixed seeds; no personal media, browser videos, private screenshots, exports, or logs may become CI artifacts. Failure artifacts are synthetic-only and retained seven days.

`docs/implementation-backlog.md` will use the requested objective/dependencies/scope/files/migrations/data/tests/acceptance/rollback/risks/operator-input template. Ordered implementation items are:

1. Project skeleton, `uv`/frontend locks, settings layout, health endpoints, static pipeline, container skeleton, CI, and quality gates only.
2. Closed authentication and production security settings.
3. Explicit catalog and target schema.
4. Deterministic normalization and alias audit.
5. Safe import, storage, playback derivative, regions, and recovery.
6. Range-playback compatibility experiment and fallback decision.
7. FSRS adapter and scheduler persistence.
8. Challenge policy and excerpt selector.
9. Persisted review orchestration, idempotency, audit, and undo.
10. Responsive TypeScript review experience.
11. Root-scope PWA and explicit offline behavior.
12. Progress, versioned export/import, backup, and isolated restore.
13. Security, performance, startup, and twenty-target development acceptance.
14. Application release/deployment compatibility handoff to a separate HomelabTrack phase.
15. Optional scale-to-zero evaluation after measurements.

Before committing documentation:

- Run `git diff --check` and any documentation/link/lint commands present on the PR branch; record that no such configured checks exist if that remains true.
- Validate relative links, Mermaid syntax where tooling exists, source URLs, requirement-matrix coverage, persistent-object lifecycle coverage, and backlog acceptance criteria.
- Scan literals to prove the only browser-facing production URL is `https://repertory.metrekare.cloud`.
- Verify no alternative subdomain, path-prefix deployment, public route, personal media, secrets, or implementation code entered the diff.

Stage only the confirmed planning paths, commit with `docs: add Repertory implementation plan`, push `agent/plan-repertory-architecture`, and update existing PR #1 rather than opening a duplicate. Do not merge it.

The final handoff will return PR #1’s URL, generated/updated files, selected decisions, unrun browser/restore/performance experiments, and unresolved operator inputs: Android test-device details, persistent-media capacity and backup cadence, actual Traefik compatibility/configuration, production resource measurements, and later HomelabTrack authorization.
