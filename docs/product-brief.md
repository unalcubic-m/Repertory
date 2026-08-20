# Repertory product brief

## Product statement

Repertory helps a learner build reliable aural recognition of musical works and movements. It presents a changing excerpt from a user-provided recording, asks for a typed answer, reveals the expected identity, records an Anki-style self-rating, and schedules the target again with FSRS.

The product is not a normal flashcard player with one saved clip per card. It is a repertoire-recognition system: the recording is the source, the work or movement is the memory target, and each review creates a temporary challenge from a different valid region.

## Primary user and operating model

The initial product is for one owner using a responsive web application from desktop and Android. It is self-hosted, private to the home LAN and approved WireGuard clients, and installable as a PWA. The data model should not make future multi-user support impossible, but multi-user administration is not an MVP objective.

## Core learning loop

1. The learner imports an audio file they are allowed to use.
2. They describe the composer, work, optional parent collection, optional movement, recording, canonical answer, and accepted aliases.
3. Repertory selects a due recognition target.
4. It chooses a valid random excerpt region and a duration appropriate to the target's current challenge level.
5. The browser plays the excerpt without displaying identifying metadata.
6. The learner types the answer and submits it.
7. Repertory checks the normalized answer against the canonical answer and explicit aliases.
8. The canonical answer and useful context are revealed.
9. The learner rates the recall as Again, Hard, Good, or Easy.
10. FSRS updates the target's next due date; the separate excerpt policy updates future challenge difficulty.

## MVP capabilities

### 1. Private account and setup

- Closed registration.
- One owner account created through an explicit bootstrap process.
- Normal Django session authentication and CSRF protection.
- Logout, password change, and safe session expiry.
- No dependency on public identity providers for the private MVP.

### 2. Repertoire library

- Create, edit, archive, and search composers, works, movements, recordings, and recognition targets.
- Represent collections with child works where useful; for example, *The Four Seasons* can contain *Spring*, *Summer*, *Autumn*, and *Winter*, each of which can have movements.
- Attach one or more recordings to the same recognition target without creating a separate memory card for every performance.
- Store a canonical answer plus explicit accepted aliases such as `Brandenburg 3`, `Brandenburg Concerto No. 3`, and localized title variants.
- Preserve catalogue numbers, key, opus number, nickname, period, and notes as optional metadata rather than mandatory answer text.
- Archive targets without deleting review history.

### 3. Audio import and validation

- Upload MP3 first; add other browser-compatible formats only after tested support is documented.
- Enforce configurable upload limits at proxy and application layers.
- Validate extension, detected media type, decodability, and duration.
- Read useful tags with Mutagen but never trust tags as the canonical answer without user confirmation.
- Obtain reliable duration and technical metadata with ffprobe when necessary.
- Store original audio outside the Git repository on governed persistent storage.
- Detect or allow the user to mark unusable intro/outro regions such as silence, applause, spoken announcements, or tuning.
- Make import failure recoverable and avoid orphaned files.

### 4. Review queue and FSRS

- Use FSRS 6 behind an application-owned scheduler interface so library details do not leak throughout the codebase.
- Keep scheduler state per user and recognition target.
- Store review timestamps in UTC.
- Support Again, Hard, Good, and Easy ratings after answer reveal.
- Show the number due today and allow a bounded study session.
- Preserve append-only review logs sufficient to rebuild or audit scheduler state.
- Support undoing the immediately previous accidental rating through an explicit, tested operation rather than editing history invisibly.
- Do not optimize personal FSRS parameters until enough review history exists and the optimizer workflow is independently designed.

### 5. Random excerpt generation

- A review chooses a temporary tuple such as `(audio asset, start time, duration)`; it does not create a permanent clip file by default.
- Random starts must stay inside valid playable windows and leave enough material for the chosen duration.
- Avoid recent start regions for the same target so repeated reviews do not teach one location.
- Exclude configured unusable regions.
- Never reveal a source filename, title tag, album tag, URL, or media artwork before the answer is submitted.
- Prefer authenticated HTTP range delivery and browser seeking for the first implementation.
- Retain a tested FFmpeg-generated excerpt fallback only if browser seeking proves inaccurate on supported devices.

### 6. Adaptive challenge policy

FSRS and excerpt difficulty are separate state machines.

FSRS decides **when** the target returns. The challenge policy decides **what the next audio question sounds like**.

The first implementation should use configurable duration bands rather than a formula that is difficult to explain. An example progression, to be tested rather than treated as final, is:

| Challenge level | Example randomized duration |
| --- | --- |
| 0 — introductory | 30–45 seconds |
| 1 | 22–32 seconds |
| 2 | 15–24 seconds |
| 3 | 10–16 seconds |
| 4 | 7–11 seconds |
| 5 — advanced | 4–8 seconds |

Policy expectations:

- New or lapsed targets become easier.
- Consistently successful reviews can become harder.
- Again should normally reduce the challenge level.
- Hard should not increase difficulty.
- Good may increase difficulty after sufficient evidence.
- Easy may increase it faster, subject to safeguards.
- Replaying the same excerpt or requesting a hint may be recorded, but must not silently decide the FSRS rating.
- Minimum duration and progression must be configurable.
- The algorithm must be deterministic given its recorded inputs except for the deliberately random excerpt selection.

### 7. Typed answer matching

- Use Unicode normalization, case folding, whitespace collapse, and configurable punctuation normalization.
- Match only the canonical answer and explicit aliases in the MVP.
- Show which alias matched.
- Do not accept an answer merely because an embedding, language model, or fuzzy score says it is semantically close.
- Permit the learner to mark a rejected answer as a new alias after reveal, with an explicit confirmation and audit trail.
- Composer recognition should be a separate configurable prompt rather than silently requiring composer text in every title answer.

### 8. Review experience

- Mobile-first, keyboard-friendly layout.
- A single obvious play/replay control.
- The typed answer field receives focus automatically after playback begins or ends according to the selected UX test result.
- Pressing Enter submits the answer but never accidentally applies a recall rating.
- The answer side can show composer, work hierarchy, movement, recording, optional notes, and a link to play more of the recording.
- Rating controls are clearly separate from answer choices.
- The next review loads without a full application restart.
- Audio must stop cleanly when navigating away or submitting.
- Accessibility includes semantic controls, visible focus, usable labels, reduced-motion respect, and sufficient contrast.

### 9. Progress and data portability

- Basic counts: due, new, learned, lapsed, and review history.
- Per-target last review, next due, current challenge level, and recent accuracy.
- Export metadata, aliases, scheduler state, and review logs in a documented machine-readable format.
- Export must not require exporting the original audio files in order to preserve learning history.
- A restore/import path must be tested before production acceptance.

### 10. PWA behavior

- Responsive browser application with a manifest and installable home-screen experience.
- Online-first for the MVP.
- Do not cache private audio or authenticated HTML indiscriminately in a service worker.
- Provide an explicit offline state rather than stale or misleading review data.
- Native Android and desktop applications are out of scope.

## Conceptual domain model

The implementation plan must refine this model before migrations are written:

- **User** — owner of library and review state.
- **Composer** — canonical name and aliases.
- **Work** — title, optional parent work/collection, catalogue metadata, key, nickname, and notes.
- **Movement** — ordered child of a work with title/tempo marking and optional number.
- **Recording** — performance metadata independent of the original file.
- **AudioAsset** — original stored file, technical metadata, checksum, duration, and permitted regions.
- **RecognitionTarget** — the work or movement the user is expected to identify and its prompt configuration.
- **AnswerAlias** — canonical or accepted normalized answer for one target.
- **SchedulerState** — FSRS state owned by one user and target.
- **ChallengeState** — excerpt difficulty state owned by one user and target.
- **ReviewLog** — immutable event describing question parameters, submitted answer, match result, replay/hint events, rating, scheduler transition, and challenge transition.

Avoid a generic schema so abstract that ordinary Django constraints become impossible. The plan should compare a small explicit relational model against any proposed polymorphic alternative.

## Important edge cases

- A full recording contains several movements, but the learner wants to identify the work only.
- One movement has its own audio file while another recording contains the entire work.
- A recording is shorter than the currently selected duration band.
- Long silence or applause exists at the beginning or end.
- Variable-bitrate MP3 seeking is imprecise on one browser.
- The same title exists for different works or composers.
- The answer is correct under a user-approved short alias but not under the canonical title.
- The user refreshes mid-review, opens two review tabs, or submits twice.
- The application sleeps while the review page is open.
- An upload is interrupted or a file disappears from storage.
- The database is restored without its matching audio storage, or vice versa.
- Clock or timezone behavior changes.

## Non-goals for the first release

- Downloading recordings from YouTube, Spotify, Apple Music, or other services.
- Distributing or publicly sharing user-supplied music.
- Public account registration or a hosted multi-tenant service.
- Automatic identification of arbitrary music like Shazam.
- Music-theory interval/chord dictation.
- Score following, score display, or instrument stem separation.
- Native mobile apps.
- Social features, leaderboards, or shared public decks.
- LLM-based answer grading.
- Redis, Celery, a permanent background worker, or scheduled notifications.
- Offline-first synchronization.

## MVP acceptance outcome

The MVP is useful when the owner can privately import at least twenty works or movements, complete a phone-based study session using changing excerpts and typed answers, see FSRS-driven due dates and adaptive duration changes, restart/recreate the application without data loss, export and restore learning data, and verify that no media or application path is exposed publicly.