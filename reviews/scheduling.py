from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fsrs import Card, Rating, Scheduler


@dataclass(frozen=True)
class ScheduleResult:
    card_json: str
    review_log_json: str
    due_at: datetime


class FsrsScheduler:
    """Small application-owned boundary around py-fsrs 6."""

    def __init__(self) -> None:
        self._scheduler = Scheduler(
            desired_retention=0.9,
            learning_steps=(timedelta(minutes=1), timedelta(minutes=10)),
            relearning_steps=(timedelta(minutes=10),),
            maximum_interval=36_500,
            enable_fuzzing=False,
        )

    def apply(self, card_json: str, rating_value: int, reviewed_at: datetime) -> ScheduleResult:
        if reviewed_at.tzinfo is None:
            raise ValueError("The review time must be timezone-aware.")
        reviewed_at = reviewed_at.astimezone(UTC)
        card = Card.from_json(card_json) if card_json else Card()
        rating = Rating(rating_value)
        updated_card, review_log = self._scheduler.review_card(
            card=card,
            rating=rating,
            review_datetime=reviewed_at,
        )
        return ScheduleResult(
            card_json=updated_card.to_json(),
            review_log_json=review_log.to_json(),
            due_at=updated_card.due,
        )
