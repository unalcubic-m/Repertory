import pytest
from django.core.exceptions import ValidationError

from library.forms import PartForm, format_timecode, parse_timecode
from reviews.models import StudyState


@pytest.mark.parametrize(
    ("value", "milliseconds"),
    [("83.5", 83_500), ("1:23.500", 83_500), ("1:01:02", 3_662_000)],
)
def test_parse_timecode(value: str, milliseconds: int) -> None:
    assert parse_timecode(value) == milliseconds


def test_invalid_timecode_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_timecode("1:90")


def test_format_timecode() -> None:
    assert format_timecode(83_500) == "1:23.5"


@pytest.mark.django_db
def test_part_form_creates_aliases_and_beginning_frontier(part) -> None:
    recording = part.recording
    form = PartForm(
        {
            "title": "II. Adagio",
            "start": "6:00",
            "end": "8:30",
            "canonical_answer": "Brandenburg 3 Adagio",
            "aliases": "Brandenburg Adagio\nBWV 1048 Adagio",
        },
        recording=recording,
    )

    assert form.is_valid(), form.errors
    created = form.save(part.owner)

    assert created.start_ms == 360_000
    assert created.end_ms == 510_000
    assert created.aliases.count() == 2
    assert StudyState.objects.get(part=created).frontier_ms == 60_000


@pytest.mark.django_db
def test_part_form_edits_boundaries_without_erasing_study_history(part) -> None:
    state = part.study_state
    state.frontier_ms = 200_000
    state.review_count = 4
    state.save()
    form = PartForm(
        {
            "title": "I. Allegro",
            "start": "1:30",
            "end": "4:00",
            "canonical_answer": "Brandenburg 3 Allegro",
            "aliases": "BWV 1048 Allegro",
        },
        recording=part.recording,
        instance=part,
    )

    assert form.is_valid(), form.errors
    updated = form.save(part.owner)
    state.refresh_from_db()

    assert updated.pk == part.pk
    assert updated.start_ms == 90_000
    assert updated.end_ms == 240_000
    assert updated.aliases.count() == 1
    assert state.review_count == 4
    assert state.frontier_ms == 150_000
