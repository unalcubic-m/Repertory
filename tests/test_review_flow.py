from datetime import UTC, datetime

import pytest
from django.urls import reverse

from library.answers import normalize_answer
from library.models import AnswerAlias
from reviews.models import ReviewLog, ReviewSession
from reviews.scheduling import FsrsScheduler


@pytest.mark.django_db
def test_fsrs_adapter_persists_utc_due_date() -> None:
    reviewed_at = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)

    result = FsrsScheduler().apply("", ReviewLog.Rating.GOOD, reviewed_at)

    assert result.due_at.tzinfo is not None
    assert result.due_at > reviewed_at
    assert '"due"' in result.card_json


@pytest.mark.django_db
def test_question_hides_identity_then_reveals_and_rates(client, owner, part) -> None:
    AnswerAlias.objects.create(
        owner=owner,
        part=part,
        value="Brandenburg 3",
        normalized_value=normalize_answer("Brandenburg 3"),
    )
    client.force_login(owner)

    question = client.get(reverse("reviews:study"))
    session = ReviewSession.objects.get(owner=owner)

    assert question.status_code == 200
    body = question.content.decode()
    assert part.canonical_answer not in body
    assert part.recording.work.title not in body
    assert part.recording.original_filename not in body

    reveal = client.post(
        reverse("reviews:answer", args=[session.public_id]),
        {"answer": "brandenburg 3", "replay_count": 0},
        follow=True,
    )
    session.refresh_from_db()

    assert session.stage == ReviewSession.Stage.REVEALED
    assert session.answer_accepted is True
    assert part.canonical_answer in reveal.content.decode()
    before_frontier = part.study_state.frontier_ms

    completed = client.post(reverse("reviews:rate", args=[session.public_id]), {"rating": 3})
    session.refresh_from_db()
    part.study_state.refresh_from_db()

    assert completed.status_code == 302
    assert session.stage == ReviewSession.Stage.COMPLETED
    assert ReviewLog.objects.filter(session=session, rating=ReviewLog.Rating.GOOD).count() == 1
    assert part.study_state.frontier_ms > before_frontier
    assert part.study_state.due_at > session.completed_at


@pytest.mark.django_db
def test_rating_cannot_happen_before_reveal(client, owner, part) -> None:
    client.force_login(owner)
    client.get(reverse("reviews:study"))
    session = ReviewSession.objects.get(owner=owner)

    client.post(reverse("reviews:rate", args=[session.public_id]), {"rating": 4})

    session.refresh_from_db()
    assert session.stage == ReviewSession.Stage.QUESTION
    assert ReviewLog.objects.count() == 0


@pytest.mark.django_db
def test_duplicate_rating_does_not_create_a_second_transition(client, owner, part) -> None:
    client.force_login(owner)
    client.get(reverse("reviews:study"))
    session = ReviewSession.objects.get(owner=owner)
    client.post(
        reverse("reviews:answer", args=[session.public_id]),
        {"answer": "not sure", "replay_count": 0},
    )

    client.post(reverse("reviews:rate", args=[session.public_id]), {"rating": 2})
    client.post(reverse("reviews:rate", args=[session.public_id]), {"rating": 2})
    client.post(reverse("reviews:rate", args=[session.public_id]), {"rating": 4})

    assert ReviewLog.objects.filter(session=session).count() == 1
    assert ReviewLog.objects.get(session=session).rating == ReviewLog.Rating.HARD


@pytest.mark.django_db
def test_audio_is_authenticated_and_supports_ranges(client, owner, part) -> None:
    client.force_login(owner)
    client.get(reverse("reviews:study"))
    session = ReviewSession.objects.get(owner=owner)
    url = reverse("reviews:audio", args=[session.public_id])

    client.logout()
    assert client.get(url).status_code == 302

    client.force_login(owner)
    response = client.get(url, HTTP_RANGE="bytes=2-5")
    assert response.status_code == 206
    assert b"".join(response.streaming_content) == b"2345"


@pytest.mark.django_db
def test_review_log_is_append_only(owner, part) -> None:
    client_session = ReviewSession.objects.create(
        owner=owner,
        part=part,
        stage=ReviewSession.Stage.COMPLETED,
        excerpt_start_ms=part.start_ms,
        excerpt_duration_ms=30_000,
        frontier_snapshot_ms=60_000,
        challenge_level_snapshot=0,
        expires_at=part.created_at,
    )
    log = ReviewLog.objects.create(
        owner=owner,
        part=part,
        session=client_session,
        reviewed_at=part.created_at,
        rating=3,
        submitted_answer="answer",
        normalized_answer="answer",
        answer_accepted=True,
        excerpt_start_ms=part.start_ms,
        excerpt_duration_ms=30_000,
        scheduler_after="{}",
        fsrs_review_log="{}",
        challenge_before={},
        challenge_after={},
    )

    log.matched_answer = "changed"
    with pytest.raises(RuntimeError, match="append-only"):
        log.save()
