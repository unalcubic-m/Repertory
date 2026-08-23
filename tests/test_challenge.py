import random

import pytest

from reviews.challenge import apply_challenge_result, select_excerpt
from reviews.models import ReviewLog


@pytest.mark.django_db
def test_excerpt_stays_in_beginning_frontier(part) -> None:
    state = part.study_state

    excerpt = select_excerpt(part, state, random.Random(7))

    assert part.start_ms <= excerpt.start_ms
    assert excerpt.start_ms + excerpt.duration_ms <= part.start_ms + 60_000
    assert 30_000 <= excerpt.duration_ms <= 45_000


@pytest.mark.django_db
def test_good_reviews_expand_frontier_and_eventually_raise_difficulty(part) -> None:
    state = part.study_state

    apply_challenge_result(
        state,
        part_duration_ms=part.duration_ms,
        rating=ReviewLog.Rating.GOOD,
        answer_accepted=True,
        replay_count=0,
    )
    assert state.frontier_ms == 90_000
    assert state.challenge_level == 0

    apply_challenge_result(
        state,
        part_duration_ms=part.duration_ms,
        rating=ReviewLog.Rating.GOOD,
        answer_accepted=True,
        replay_count=0,
    )
    assert state.frontier_ms == 120_000
    assert state.challenge_level == 1


@pytest.mark.django_db
def test_again_makes_excerpt_easier_without_rewinding_frontier(part) -> None:
    state = part.study_state
    state.challenge_level = 3
    state.frontier_ms = 180_000

    apply_challenge_result(
        state,
        part_duration_ms=part.duration_ms,
        rating=ReviewLog.Rating.AGAIN,
        answer_accepted=False,
        replay_count=1,
    )

    assert state.challenge_level == 1
    assert state.frontier_ms == 180_000
    assert state.lapse_count == 1
