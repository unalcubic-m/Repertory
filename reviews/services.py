import random
import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.utils import timezone

from library.answers import match_answer, normalize_answer

from .challenge import apply_challenge_result, challenge_snapshot, select_excerpt
from .models import ReviewLog, ReviewSession, StudyState
from .scheduling import FsrsScheduler

SESSION_LIFETIME = timedelta(hours=2)


@transaction.atomic
def get_or_create_session(owner: User) -> ReviewSession | None:
    now = timezone.now()
    ReviewSession.objects.filter(
        owner=owner,
        stage__in=[ReviewSession.Stage.QUESTION, ReviewSession.Stage.REVEALED],
        expires_at__lte=now,
    ).update(stage=ReviewSession.Stage.EXPIRED)
    active = (
        ReviewSession.objects.filter(
            owner=owner,
            stage__in=[ReviewSession.Stage.QUESTION, ReviewSession.Stage.REVEALED],
            expires_at__gt=now,
        )
        .select_related(
            "part", "part__recording", "part__recording__work", "part__recording__work__composer"
        )
        .prefetch_related("part__aliases")
        .first()
    )
    if active is not None:
        return active

    state = (
        StudyState.objects.select_for_update()
        .filter(
            owner=owner,
            due_at__lte=now,
            part__archived=False,
            part__recording__archived=False,
            part__recording__status="ready",
        )
        .select_related("part", "part__recording")
        .order_by("due_at", "id")
        .first()
    )
    if state is None:
        return None

    excerpt = select_excerpt(state.part, state, random.SystemRandom())
    try:
        return ReviewSession.objects.create(
            owner=owner,
            part=state.part,
            excerpt_start_ms=excerpt.start_ms,
            excerpt_duration_ms=excerpt.duration_ms,
            frontier_snapshot_ms=state.frontier_ms,
            challenge_level_snapshot=state.challenge_level,
            expires_at=now + SESSION_LIFETIME,
        )
    except IntegrityError:
        return ReviewSession.objects.get(
            owner=owner,
            stage__in=[ReviewSession.Stage.QUESTION, ReviewSession.Stage.REVEALED],
        )


@transaction.atomic
def reveal_answer(
    *, owner: User, session_id: uuid.UUID | str, submitted_answer: str, replay_count: int
) -> ReviewSession:
    session = (
        ReviewSession.objects.select_for_update()
        .select_related("part")
        .prefetch_related("part__aliases")
        .get(owner=owner, public_id=session_id)
    )
    if session.stage == ReviewSession.Stage.REVEALED:
        if session.submitted_answer != submitted_answer or session.replay_count != min(
            100, replay_count
        ):
            raise ValueError("This answer has already been revealed with different input.")
        return session
    if session.stage != ReviewSession.Stage.QUESTION or session.expires_at <= timezone.now():
        raise ValueError("This review is no longer open.")
    accepted, matched = match_answer(session.part, submitted_answer)
    session.submitted_answer = submitted_answer
    session.normalized_answer = normalize_answer(submitted_answer)
    session.answer_accepted = accepted
    session.matched_answer = matched or ""
    session.replay_count = min(100, replay_count)
    session.revealed_at = timezone.now()
    session.stage = ReviewSession.Stage.REVEALED
    session.save(
        update_fields=[
            "submitted_answer",
            "normalized_answer",
            "answer_accepted",
            "matched_answer",
            "replay_count",
            "revealed_at",
            "stage",
        ]
    )
    return session


@transaction.atomic
def rate_answer(*, owner: User, session_id: uuid.UUID | str, rating: int) -> ReviewLog:
    now = timezone.now()
    session = (
        ReviewSession.objects.select_for_update()
        .select_related("part")
        .get(owner=owner, public_id=session_id)
    )
    if session.stage == ReviewSession.Stage.COMPLETED:
        existing_log = session.review_log
        if existing_log.rating != rating:
            raise ValueError("This review has already been rated differently.")
        return existing_log
    if session.stage != ReviewSession.Stage.REVEALED or session.expires_at <= now:
        raise ValueError("Reveal the answer before rating this review.")

    state = StudyState.objects.select_for_update().get(owner=owner, part=session.part)
    scheduler_before = state.fsrs_card_json
    challenge_before = challenge_snapshot(state)
    schedule = FsrsScheduler().apply(scheduler_before, rating, now)
    apply_challenge_result(
        state,
        part_duration_ms=session.part.duration_ms,
        rating=rating,
        answer_accepted=bool(session.answer_accepted),
        replay_count=session.replay_count,
    )
    state.fsrs_card_json = schedule.card_json
    state.due_at = schedule.due_at
    state.last_review_at = now
    state.save()
    challenge_after = challenge_snapshot(state)
    review_log = ReviewLog.objects.create(
        owner=owner,
        part=session.part,
        session=session,
        reviewed_at=now,
        rating=rating,
        submitted_answer=session.submitted_answer,
        normalized_answer=session.normalized_answer,
        answer_accepted=bool(session.answer_accepted),
        matched_answer=session.matched_answer,
        replay_count=session.replay_count,
        excerpt_start_ms=session.excerpt_start_ms,
        excerpt_duration_ms=session.excerpt_duration_ms,
        scheduler_before=scheduler_before,
        scheduler_after=schedule.card_json,
        fsrs_review_log=schedule.review_log_json,
        challenge_before=challenge_before,
        challenge_after=challenge_after,
    )
    session.stage = ReviewSession.Stage.COMPLETED
    session.completed_at = now
    session.save(update_fields=["stage", "completed_at"])
    return review_log
