import random
from dataclasses import dataclass

from library.models import Part

from .models import ReviewLog, StudyState

DURATION_BANDS_MS = (
    (30_000, 45_000),
    (22_000, 32_000),
    (15_000, 24_000),
    (10_000, 16_000),
    (7_000, 11_000),
    (4_000, 8_000),
)


@dataclass(frozen=True)
class Excerpt:
    start_ms: int
    duration_ms: int


def select_excerpt(part: Part, state: StudyState, rng: random.Random) -> Excerpt:
    available_ms = min(part.duration_ms, max(4_000, state.frontier_ms))
    minimum, maximum = DURATION_BANDS_MS[state.challenge_level]
    maximum = min(maximum, available_ms)
    minimum = min(minimum, maximum)
    duration = rng.randint(minimum, maximum)
    latest_relative_start = available_ms - duration
    recent_starts = list(
        ReviewLog.objects.filter(part=part)
        .order_by("-reviewed_at")
        .values_list("excerpt_start_ms", flat=True)[:5]
    )

    relative_start = 0
    for _ in range(12):
        candidate = rng.randint(0, latest_relative_start) if latest_relative_start else 0
        absolute_candidate = part.start_ms + candidate
        minimum_distance = min(10_000, max(2_000, duration // 2))
        if all(abs(absolute_candidate - recent) >= minimum_distance for recent in recent_starts):
            relative_start = candidate
            break
        relative_start = candidate
    return Excerpt(start_ms=part.start_ms + relative_start, duration_ms=duration)


def challenge_snapshot(state: StudyState) -> dict[str, int]:
    return {
        "challenge_level": state.challenge_level,
        "frontier_ms": state.frontier_ms,
        "success_credit": state.success_credit,
        "reviews_at_level": state.reviews_at_level,
        "review_count": state.review_count,
        "lapse_count": state.lapse_count,
    }


def apply_challenge_result(
    state: StudyState,
    *,
    part_duration_ms: int,
    rating: int,
    answer_accepted: bool,
    replay_count: int,
) -> None:
    state.review_count += 1
    state.reviews_at_level += 1
    old_level = state.challenge_level
    clean_success = (
        rating in (ReviewLog.Rating.GOOD, ReviewLog.Rating.EASY)
        and answer_accepted
        and replay_count == 0
    )

    if rating == ReviewLog.Rating.AGAIN:
        state.challenge_level = max(0, state.challenge_level - 2)
        state.lapse_count += 1
        state.success_credit = 0
    elif rating == ReviewLog.Rating.HARD:
        state.challenge_level = max(0, state.challenge_level - 1)
        state.success_credit = 0
    elif clean_success:
        state.success_credit += 2 if rating == ReviewLog.Rating.EASY else 1
        if state.success_credit >= 2 and state.reviews_at_level >= 2:
            state.challenge_level = min(5, state.challenge_level + 1)
            state.success_credit = 0
    else:
        state.success_credit = 0

    if rating in (ReviewLog.Rating.GOOD, ReviewLog.Rating.EASY) and answer_accepted:
        step = max(30_000, part_duration_ms // 10)
        if rating == ReviewLog.Rating.EASY:
            step *= 2
        state.frontier_ms = min(part_duration_ms, state.frontier_ms + step)

    if state.challenge_level != old_level:
        state.reviews_at_level = 0
