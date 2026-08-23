import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from library.models import Composer, Part, Recording, Work
from reviews.models import StudyState


@pytest.fixture
def owner(db):
    return get_user_model().objects.create_user(username="owner", password="a-long-test-password")


@pytest.fixture
def part(owner, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    composer = Composer.objects.create(owner=owner, name="Johann Sebastian Bach")
    work = Work.objects.create(owner=owner, composer=composer, title="Brandenburg Concerto No. 3")
    recording = Recording(
        owner=owner,
        work=work,
        label="Synthetic performance",
        original_filename="private-title.mp3",
        content_type="audio/mpeg",
        size_bytes=128,
        duration_ms=600_000,
        sha256="a" * 64,
    )
    recording.original_file.save("original.mp3", ContentFile(b"original"), save=False)
    recording.playback_file.save("playback.mp3", ContentFile(b"0123456789" * 20), save=False)
    recording.save()
    part = Part.objects.create(
        owner=owner,
        recording=recording,
        sequence=1,
        title="I. Allegro moderato",
        start_ms=60_000,
        end_ms=360_000,
        canonical_answer="Brandenburg Concerto No. 3 — Allegro moderato",
    )
    StudyState.objects.create(owner=owner, part=part, frontier_ms=60_000)
    return part
