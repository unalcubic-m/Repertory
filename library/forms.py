import re
from typing import Any

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction

from .answers import normalize_answer
from .audio import import_recording
from .models import AnswerAlias, Part, Recording

TIME_PATTERN = re.compile(
    r"^(?:(?P<hours>\d+):)?(?P<minutes>\d{1,2}):(?P<seconds>\d{1,2}(?:\.\d{1,3})?)$"
)


def parse_timecode(value: str) -> int:
    value = value.strip()
    if value.replace(".", "", 1).isdigit():
        return round(float(value) * 1000)
    match = TIME_PATTERN.fullmatch(value)
    if match is None:
        raise ValidationError("Use seconds, MM:SS, or HH:MM:SS (for example 1:23.500).")
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes"))
    seconds = float(match.group("seconds"))
    if minutes >= 60 or seconds >= 60:
        raise ValidationError("Minutes and seconds must be below 60.")
    return round((hours * 3600 + minutes * 60 + seconds) * 1000)


def format_timecode(milliseconds: int) -> str:
    seconds = milliseconds / 1000
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{int(hours)}:{int(minutes):02d}:{seconds:06.3f}".rstrip("0").rstrip(".")
    return f"{int(minutes)}:{seconds:06.3f}".rstrip("0").rstrip(".")


class RecordingImportForm(forms.Form):
    composer = forms.CharField(max_length=200)
    work_title = forms.CharField(max_length=240, label="Work title")
    recording_label = forms.CharField(
        max_length=200,
        required=False,
        help_text="Optional performer, orchestra, or edition label.",
    )
    audio_file = forms.FileField(
        label="MP3 file",
        widget=forms.ClearableFileInput(attrs={"accept": ".mp3,audio/mpeg"}),
    )

    def save(self, owner: User) -> Recording:
        return import_recording(
            owner=owner,
            composer_name=self.cleaned_data["composer"],
            work_title=self.cleaned_data["work_title"],
            recording_label=self.cleaned_data["recording_label"],
            upload=self.cleaned_data["audio_file"],
        )


class PartForm(forms.Form):
    title = forms.CharField(
        max_length=240,
        help_text="For example: I. Allegro moderato",
    )
    start = forms.CharField(initial="0:00", help_text="Seconds or MM:SS")
    end = forms.CharField(help_text="Seconds or MM:SS")
    canonical_answer = forms.CharField(
        max_length=256,
        help_text="The answer you want to type during review.",
    )
    aliases = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Optional accepted answers, one per line.",
    )

    def __init__(
        self,
        *args: Any,
        recording: Recording,
        instance: Part | None = None,
        **kwargs: Any,
    ) -> None:
        self.recording = recording
        self.instance = instance
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            if instance is not None:
                self.initial.update(
                    {
                        "title": instance.title,
                        "start": format_timecode(instance.start_ms),
                        "end": format_timecode(instance.end_ms),
                        "canonical_answer": instance.canonical_answer,
                        "aliases": "\n".join(
                            instance.aliases.filter(active=True).values_list("value", flat=True)
                        ),
                    }
                )
            else:
                self.initial.setdefault("end", format_timecode(recording.duration_ms))

    def clean_start(self) -> int:
        return parse_timecode(self.cleaned_data["start"])

    def clean_end(self) -> int:
        return parse_timecode(self.cleaned_data["end"])

    def clean_aliases(self) -> list[tuple[str, str]]:
        values = [
            line.strip() for line in self.cleaned_data["aliases"].splitlines() if line.strip()
        ]
        aliases: list[tuple[str, str]] = []
        seen: set[str] = set()
        for value in values:
            normalized = normalize_answer(value)
            if not normalized:
                raise ValidationError("An alias cannot normalize to an empty answer.")
            if normalized in seen:
                raise ValidationError("Aliases must be distinct after normalization.")
            seen.add(normalized)
            aliases.append((value, normalized))
        return aliases

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        start = cleaned.get("start")
        end = cleaned.get("end")
        canonical = cleaned.get("canonical_answer")
        if start is not None and end is not None:
            if end <= start:
                self.add_error("end", "The end must be after the start.")
            elif end - start < 4_000:
                self.add_error("end", "A study part must be at least four seconds long.")
            elif end > self.recording.duration_ms:
                self.add_error("end", "The end is after this recording finishes.")
        if canonical and not normalize_answer(canonical):
            self.add_error("canonical_answer", "The answer cannot normalize to empty text.")
        return cleaned

    @transaction.atomic
    def save(self, owner: User) -> Part:
        if self.instance is None:
            sequence = (
                self.recording.parts.order_by("-sequence")
                .values_list("sequence", flat=True)
                .first()
                or 0
            ) + 1
            part = Part(owner=owner, recording=self.recording, sequence=sequence)
        else:
            part = self.instance
        part.title = self.cleaned_data["title"]
        part.start_ms = self.cleaned_data["start"]
        part.end_ms = self.cleaned_data["end"]
        part.canonical_answer = self.cleaned_data["canonical_answer"]
        part.full_clean()
        part.save()
        part.aliases.all().delete()
        aliases = [
            AnswerAlias(
                owner=owner,
                part=part,
                value=value,
                normalized_value=normalized,
            )
            for value, normalized in self.cleaned_data["aliases"]
            if normalized != normalize_answer(part.canonical_answer)
        ]
        AnswerAlias.objects.bulk_create(aliases)
        if self.instance is None:
            from reviews.models import StudyState

            StudyState.objects.create(
                owner=owner,
                part=part,
                frontier_ms=min(part.duration_ms, 60_000),
            )
        else:
            state = part.study_state
            state.frontier_ms = min(state.frontier_ms, part.duration_ms)
            state.save(update_fields=["frontier_ms", "updated_at"])
        return part
