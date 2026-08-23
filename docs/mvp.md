# Basic MVP behavior

Status: implemented on `agent/basic-mvp` on 2026-08-23. This is a development MVP, not production
deployment authorization.

## Owner workflow

1. Create the sole owner account with Django's `createsuperuser` command.
2. Import an MP3 with composer, work title, and an optional performance label.
3. Open the recording and listen through the protected management player.
4. Mark one or more named parts with start/end timecodes. The “use current time” controls copy the
   player's position into the form.
5. Configure a canonical typed answer and zero or more explicit aliases for each part.
6. Open Study, play the anonymous excerpt, type a guess, and reveal the answer.
7. Rate recall Again, Hard, Good, or Easy. Only this explicit rating is sent to FSRS.

Marked parts can be edited. Existing review history is retained when a title, boundary, answer, or alias
is corrected.

## Beginning-first excerpt policy

Each part has a learning frontier measured from its configured start:

- initial frontier: the shorter of 60 seconds or the complete part;
- Good with an accepted answer: expand by the larger of 30 seconds or 10% of the part;
- Easy with an accepted answer: expand by twice that amount;
- Hard or Again: do not erase previously reached material;
- the frontier never exceeds the part end.

The selector chooses a fresh start inside `[part start, part start + frontier]` and uses the configured
challenge-level duration band. It tries to avoid starts used in the five latest completed reviews. A
short part uses its longest valid excerpt, down to the four-second minimum.

Challenge levels and duration bands are independent of FSRS:

| Level | Duration |
| --- | --- |
| 0 | 30–45 seconds |
| 1 | 22–32 seconds |
| 2 | 15–24 seconds |
| 3 | 10–16 seconds |
| 4 | 7–11 seconds |
| 5 | 4–8 seconds |

Two clean-success credits and at least two reviews at one level are required to advance. Good earns one
credit and Easy earns two. A replay or unmatched typed answer prevents an upward challenge credit, but
does not silently change the explicit FSRS rating. Again lowers challenge by two levels; Hard lowers it
by one.

## Import and media lifecycle

- `.mp3` is the only accepted extension.
- Mutagen must parse at least four seconds and no more than six hours of audio.
- The application limit is 512 MiB; the hosted platform should enforce the same or a lower request limit where configurable.
- SHA-256 rejects exact duplicate uploads for the owner.
- The original is stored under an opaque generated name and is never used on the question page.
- A second opaque copy is made and Mutagen removes ID3 metadata/artwork before browser playback.
- Import failure deletes any files created during that attempt.
- Recordings and parts use protective relationships; the ordinary UI edits or archives rather than
  deleting learning history.

Playback endpoints require the owner session and implement single HTTP byte ranges with `200`, `206`,
and `416` responses. They use `private, no-store, no-transform` and answer-neutral URLs/filenames.
Pre-reveal HTML contains no composer, work, part, canonical answer, alias, original filename, or path.

## Review transaction

Only one open review session exists for the owner. It freezes the part, excerpt start, excerpt duration,
frontier snapshot, and challenge snapshot for two hours. Refreshing resumes that session. Answer reveal
must precede rating. Rating updates the FSRS card, due time, challenge state, immutable review log, and
session completion in one database transaction. A repeated identical rating request returns the existing
log rather than creating a second transition.

Review logs reject application-level edits and deletes. All schedule timestamps are UTC-aware.

## Verification and limitations

Automated coverage includes generated CBR/VBR MP3 import and metadata stripping, answer normalization,
alias matching, timecode parsing, part creation, duplicate handling, opaque paths, beginning-frontier
selection, challenge transitions, FSRS UTC scheduling, answer secrecy, reveal/rating order, duplicate
rating protection, append-only review logs, authenticated playback, and byte ranges.

The locked Python 3.13 environment, strict TypeScript build, and multi-stage `repertory:mvp` container
image have been built successfully. The image's production settings pass Django's system check while
running as UID/GID 10001.

The Render-targeted image was also exercised with a disposable Docker volume on 2026-08-23. Runtime
migrations, readiness, WhiteNoise static delivery, anonymous login redirects, and SQLite persistence
across container recreation passed. Render's remote Blueprint validator accepts the deployment shape;
live provisioning remains gated on payment information for the Starter service and persistent disk.

Still required after this basic MVP:

- physical-browser playback timing for the generated CBR/VBR fixtures;
- physical Android Chromium and desktop Chromium playback timing evidence;
- immediate accidental-rating undo;
- alias-change audit rows;
- richer composer/work/recording management, archive controls, search, and progress pages;
- versioned export/import and an isolated database/media restore test;
- installable PWA behavior and browser automation;
- persistent Render startup, public-login boundary, backup, and restore acceptance in the deployment
  phase.
