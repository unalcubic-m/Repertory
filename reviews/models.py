import uuid
from collections.abc import Iterable

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.base import ModelBase
from django.utils import timezone

from library.models import Part


class StudyState(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    part = models.OneToOneField(Part, on_delete=models.PROTECT, related_name="study_state")
    fsrs_card_json = models.TextField(blank=True)
    due_at = models.DateTimeField(default=timezone.now, db_index=True)
    last_review_at = models.DateTimeField(blank=True, null=True)
    challenge_level = models.PositiveSmallIntegerField(default=0)
    frontier_ms = models.PositiveBigIntegerField(default=60_000)
    success_credit = models.PositiveSmallIntegerField(default=0)
    reviews_at_level = models.PositiveIntegerField(default=0)
    review_count = models.PositiveIntegerField(default=0)
    lapse_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "part"], name="unique_study_state_per_part"),
            models.CheckConstraint(
                condition=Q(challenge_level__lte=5), name="challenge_level_between_zero_and_five"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.part} due {self.due_at}"


class ReviewSession(models.Model):
    class Stage(models.TextChoices):
        QUESTION = "question", "Question"
        REVEALED = "revealed", "Revealed"
        COMPLETED = "completed", "Completed"
        EXPIRED = "expired", "Expired"

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name="review_sessions")
    stage = models.CharField(max_length=16, choices=Stage.choices, default=Stage.QUESTION)
    excerpt_start_ms = models.PositiveBigIntegerField()
    excerpt_duration_ms = models.PositiveIntegerField()
    frontier_snapshot_ms = models.PositiveBigIntegerField()
    challenge_level_snapshot = models.PositiveSmallIntegerField()
    submitted_answer = models.CharField(max_length=256, blank=True)
    normalized_answer = models.CharField(max_length=256, blank=True)
    answer_accepted = models.BooleanField(blank=True, null=True)
    matched_answer = models.CharField(max_length=256, blank=True)
    replay_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    revealed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner"],
                condition=Q(stage__in=["question", "revealed"]),
                name="one_open_review_per_owner",
            )
        ]

    def __str__(self) -> str:
        return str(self.public_id)


class ReviewLog(models.Model):
    class Rating(models.IntegerChoices):
        AGAIN = 1, "Again"
        HARD = 2, "Hard"
        GOOD = 3, "Good"
        EASY = 4, "Easy"

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name="review_logs")
    session = models.OneToOneField(
        ReviewSession, on_delete=models.PROTECT, related_name="review_log"
    )
    reviewed_at = models.DateTimeField(db_index=True)
    rating = models.PositiveSmallIntegerField(choices=Rating.choices)
    submitted_answer = models.CharField(max_length=256)
    normalized_answer = models.CharField(max_length=256)
    answer_accepted = models.BooleanField()
    matched_answer = models.CharField(max_length=256, blank=True)
    replay_count = models.PositiveSmallIntegerField(default=0)
    excerpt_start_ms = models.PositiveBigIntegerField()
    excerpt_duration_ms = models.PositiveIntegerField()
    scheduler_before = models.TextField(blank=True)
    scheduler_after = models.TextField()
    fsrs_review_log = models.TextField()
    challenge_before = models.JSONField()
    challenge_after = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reviewed_at"]
        indexes = [models.Index(fields=["owner", "part", "-reviewed_at"])]

    def save(
        self,
        *,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        if self.pk and ReviewLog.objects.filter(pk=self.pk).exists():
            raise RuntimeError("Review logs are append-only and cannot be edited.")
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    def delete(self, *args: object, **kwargs: object) -> tuple[int, dict[str, int]]:
        raise RuntimeError("Review logs are append-only and cannot be deleted.")

    def __str__(self) -> str:
        return f"{self.part}: {self.get_rating_display()}"
