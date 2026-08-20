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
6. A spaced-repetition scheduler determines the next review date, while a separate difficulty model adjusts future excerpt length.

## Key design principle

A review item represents a **piece or movement to recognize**, not one fixed audio clip. Every review should normally sample a different part of the recording so the learner recognizes the music itself rather than memorizing a particular opening.

The scheduling model and the audio-difficulty model are related but distinct:

- **Scheduling** answers: “When should this item be reviewed again?”
- **Excerpt difficulty** answers: “How much audio should the learner hear next time?”

## Initial MVP goals

- Mobile-first installable web app/PWA.
- User-supplied MP3 and other browser-compatible audio files.
- Library of works, movements, recordings, aliases, and recognition targets.
- Random, bounded excerpts with adaptive duration.
- Typed free-recall answers with normalization and explicit self-grading.
- FSRS-style spaced repetition behind a replaceable scheduler interface.
- Review history, basic progress statistics, and reliable backup/export.
- Privacy-conscious, self-hostable operation without distributing copyrighted recordings.

## Terminology

| Term | Meaning in Repertory |
| --- | --- |
| **Work** | A composition such as *The Four Seasons* or *Symphony No. 5*. |
| **Movement** | A major section inside a work, such as “I. Allegro.” |
| **Recording** | A particular performance/audio file supplied by the user. |
| **Recognition target** | The answer expected during review: a work, movement, or another configured level. |
| **Excerpt** | The temporary segment played during one review. It is not a permanent card. |

## Project documents

- [`docs/product-brief.md`](docs/product-brief.md) — product goals, requirements, and constraints
- [`docs/roadmap.md`](docs/roadmap.md) — proposed delivery phases
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — decisions that the planning phase must resolve
- [`docs/CODEX_PLANNING_PROMPT.md`](docs/CODEX_PLANNING_PROMPT.md) — planning prompt for Codex
- [`AGENTS.md`](AGENTS.md) — repository instructions for coding agents

## Media and copyright

Repertory is intended to help users study audio they are legally allowed to use. Do not commit personal music files or copyrighted commercial recordings to this repository. Tests should use generated tones, original fixtures, or appropriately licensed/public-domain audio.

## Status

The next step is an architecture and implementation plan. Code should not be scaffolded until the planning phase records the major product and technical decisions.
