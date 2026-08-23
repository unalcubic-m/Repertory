import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class OwnedModel(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Composer(OwnedModel):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="unique_composer_per_owner")
        ]

    def __str__(self) -> str:
        return self.name


class Work(OwnedModel):
    class Kind(models.TextChoices):
        COLLECTION = "collection", "Collection"
        WORK = "work", "Work"

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    composer = models.ForeignKey(Composer, on_delete=models.PROTECT, related_name="works")
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="children",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.WORK)
    title = models.CharField(max_length=240)
    catalogue_number = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["composer__name", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "composer", "parent", "title"],
                name="unique_work_title_in_parent",
            ),
            models.CheckConstraint(
                condition=~Q(id=F("parent_id")),
                name="work_cannot_parent_itself",
            ),
        ]

    def clean(self) -> None:
        if self.composer_id and self.owner_id != self.composer.owner_id:
            raise ValidationError("Composer and work must have the same owner.")
        if self.parent is not None and self.owner_id != self.parent.owner_id:
            raise ValidationError("Parent and child work must have the same owner.")

    def __str__(self) -> str:
        return self.title


def original_upload_to(instance: "Recording", filename: str) -> str:
    return f"originals/{instance.owner_id}/{uuid.uuid4().hex}.mp3"


def playback_upload_to(instance: "Recording", filename: str) -> str:
    return f"playback/{instance.owner_id}/{uuid.uuid4().hex}.mp3"


class Recording(OwnedModel):
    class Status(models.TextChoices):
        READY = "ready", "Ready"
        MISSING = "missing", "Missing"
        CORRUPT = "corrupt", "Corrupt"

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    work = models.ForeignKey(Work, on_delete=models.PROTECT, related_name="recordings")
    label = models.CharField(max_length=200, blank=True)
    original_file = models.FileField(upload_to=original_upload_to, max_length=500)
    playback_file = models.FileField(upload_to=playback_upload_to, max_length=500)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True)
    size_bytes = models.PositiveBigIntegerField()
    duration_ms = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.READY)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["work__composer__name", "work__title", "label"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "sha256"], name="unique_audio_checksum_per_owner"
            ),
            models.CheckConstraint(
                condition=Q(duration_ms__gte=4_000), name="recording_at_least_four_seconds"
            ),
            models.CheckConstraint(condition=Q(size_bytes__gt=0), name="recording_nonempty"),
        ]

    @property
    def display_name(self) -> str:
        return self.label or self.work.title

    def clean(self) -> None:
        if self.work_id and self.owner_id != self.work.owner_id:
            raise ValidationError("Work and recording must have the same owner.")

    def __str__(self) -> str:
        return f"{self.work} — {self.display_name}"


class Part(OwnedModel):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    recording = models.ForeignKey(Recording, on_delete=models.PROTECT, related_name="parts")
    sequence = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=240)
    start_ms = models.PositiveBigIntegerField(default=0)
    end_ms = models.PositiveBigIntegerField()
    canonical_answer = models.CharField(max_length=256)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["recording", "sequence", "start_ms"]
        constraints = [
            models.UniqueConstraint(
                fields=["recording", "sequence"], name="unique_part_sequence_per_recording"
            ),
            models.CheckConstraint(
                condition=Q(end_ms__gt=F("start_ms")), name="part_end_after_start"
            ),
        ]

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    def clean(self) -> None:
        errors: dict[str, str] = {}
        if self.recording_id:
            if self.owner_id != self.recording.owner_id:
                errors["recording"] = "Recording and part must have the same owner."
            if self.end_ms > self.recording.duration_ms:
                errors["end_ms"] = "The part cannot end after the recording."
        if self.end_ms - self.start_ms < 4_000:
            errors["end_ms"] = "A study part must be at least four seconds long."
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return self.title


class AnswerAlias(OwnedModel):
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name="aliases")
    value = models.CharField(max_length=256)
    normalized_value = models.CharField(max_length=256)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["value"]
        constraints = [
            models.UniqueConstraint(
                fields=["part", "normalized_value"], name="unique_normalized_alias_per_part"
            )
        ]

    def clean(self) -> None:
        if self.part_id and self.owner_id != self.part.owner_id:
            raise ValidationError("Part and alias must have the same owner.")

    def __str__(self) -> str:
        return self.value
