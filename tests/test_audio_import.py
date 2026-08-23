import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from library.audio import Mp3Details, import_recording, inspect_mp3


def test_inspect_rejects_non_mp3_extension() -> None:
    upload = SimpleUploadedFile("piece.wav", b"RIFF", content_type="audio/wav")
    with pytest.raises(ValidationError, match="Only MP3"):
        inspect_mp3(upload)


@pytest.mark.django_db
def test_import_preserves_original_and_creates_opaque_playback(owner, settings, tmp_path) -> None:
    settings.MEDIA_ROOT = tmp_path / "media"
    upload = SimpleUploadedFile(
        "Secret Symphony Title.mp3",
        b"synthetic-test-bytes",
        content_type="audio/mpeg",
    )

    def sanitized_copy(source: Path) -> Path:
        target = Path(tempfile.mkstemp(suffix=".mp3", dir=settings.MEDIA_ROOT)[1])
        shutil.copyfile(source, target)
        return target

    with (
        patch(
            "library.audio.inspect_mp3",
            return_value=Mp3Details("f" * 64, len(upload), 120_000),
        ),
        patch("library.audio._make_sanitized_copy", side_effect=sanitized_copy),
    ):
        recording = import_recording(
            owner=owner,
            composer_name="Ludwig van Beethoven",
            work_title="Symphony No. 5",
            recording_label="Test performance",
            upload=upload,
        )

    assert recording.original_filename == "Secret Symphony Title.mp3"
    assert "Secret" not in recording.original_file.name
    assert "Symphony" not in recording.playback_file.name
    assert Path(recording.original_file.path).read_bytes() == b"synthetic-test-bytes"
    assert Path(recording.playback_file.path).read_bytes() == b"synthetic-test-bytes"


@pytest.mark.django_db
def test_duplicate_import_is_rejected(owner) -> None:
    from library.models import Composer, Recording, Work

    composer = Composer.objects.create(owner=owner, name="Composer")
    work = Work.objects.create(owner=owner, composer=composer, title="Work")
    Recording.objects.create(
        owner=owner,
        work=work,
        original_file="originals/existing.mp3",
        playback_file="playback/existing.mp3",
        original_filename="existing.mp3",
        size_bytes=10,
        duration_ms=10_000,
        sha256="d" * 64,
    )
    upload = SimpleUploadedFile("again.mp3", b"same")
    with (
        patch("library.audio.inspect_mp3", return_value=Mp3Details("d" * 64, 4, 10_000)),
        pytest.raises(ValidationError, match="already imported"),
    ):
        import_recording(
            owner=owner,
            composer_name="Other",
            work_title="Other",
            recording_label="",
            upload=upload,
        )
