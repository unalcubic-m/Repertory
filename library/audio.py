import hashlib
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from mutagen import File as MutagenFile
from mutagen import MutagenError
from mutagen.mp3 import MP3

from .models import Composer, Recording, Work


@dataclass(frozen=True)
class Mp3Details:
    sha256: str
    size_bytes: int
    duration_ms: int


def _sha256(stream: IO[Any]) -> str:
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(block)
    stream.seek(0)
    return digest.hexdigest()


def inspect_mp3(upload: UploadedFile) -> Mp3Details:
    filename = upload.name or ""
    size = upload.size
    stream = upload.file
    if Path(filename).suffix.casefold() != ".mp3":
        raise ValidationError("Only MP3 files are supported in this first version.")
    if size is None or size <= 0:
        raise ValidationError("The uploaded file is empty.")
    if size > settings.REPERTORY_MAX_UPLOAD_BYTES:
        raise ValidationError("The MP3 is larger than the configured upload limit.")
    if stream is None:
        raise ValidationError("The uploaded file could not be read.")

    try:
        upload.seek(0)
        audio: Any = MP3(stream)  # type: ignore[no-untyped-call]
        duration_ms = round(float(audio.info.length) * 1000)
    except (MutagenError, OSError, ValueError) as error:
        raise ValidationError("This file is not a readable MP3 audio stream.") from error
    finally:
        upload.seek(0)

    if duration_ms < 4_000:
        raise ValidationError("The MP3 must contain at least four seconds of audio.")
    if duration_ms > settings.REPERTORY_MAX_DURATION_MS:
        raise ValidationError("The MP3 is longer than the configured duration limit.")
    return Mp3Details(_sha256(stream), size, duration_ms)


def _make_sanitized_copy(source: Path) -> Path:
    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix="repertory-playback-", suffix=".mp3", dir=media_root, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        with source.open("rb") as original:
            shutil.copyfileobj(original, temporary)
    try:
        tagged_audio = MutagenFile(temporary_path)
        if tagged_audio is None:
            raise ValidationError("The saved file is not a readable MP3.")
        tagged_audio.delete()
        verified: Any = MP3(temporary_path)  # type: ignore[no-untyped-call]
        if float(verified.info.length) < 4:
            raise ValidationError("The sanitized playback file is invalid.")
        return temporary_path
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


@transaction.atomic
def import_recording(
    *,
    owner: User,
    composer_name: str,
    work_title: str,
    recording_label: str,
    upload: UploadedFile,
) -> Recording:
    details = inspect_mp3(upload)
    duplicate = Recording.objects.filter(owner=owner, sha256=details.sha256).first()
    if duplicate is not None:
        raise ValidationError(f"This exact MP3 is already imported as {duplicate.display_name!r}.")

    composer = Composer.objects.filter(owner=owner, name__iexact=composer_name.strip()).first()
    if composer is None:
        composer = Composer.objects.create(owner=owner, name=composer_name.strip())
    work = Work.objects.filter(
        owner=owner,
        composer=composer,
        parent=None,
        title__iexact=work_title.strip(),
    ).first()
    if work is None:
        work = Work.objects.create(owner=owner, composer=composer, title=work_title.strip())

    recording = Recording(
        owner=owner,
        work=work,
        label=recording_label.strip(),
        original_filename=Path(upload.name or "upload.mp3").name[:255],
        content_type=(upload.content_type or "")[:100],
        size_bytes=details.size_bytes,
        duration_ms=details.duration_ms,
        sha256=details.sha256,
    )
    created_names: list[tuple[object, str]] = []
    temporary_path: Path | None = None
    try:
        recording.original_file.save("original.mp3", upload, save=False)
        created_names.append((recording.original_file.storage, recording.original_file.name))
        original_path = recording.original_file.path
        if not original_path:
            raise ValidationError("The original MP3 could not be stored.")
        temporary_path = _make_sanitized_copy(Path(original_path))
        with temporary_path.open("rb") as sanitized:
            recording.playback_file.save("playback.mp3", File(sanitized), save=False)
        created_names.append((recording.playback_file.storage, recording.playback_file.name))
        recording.full_clean()
        recording.save()
        return recording
    except Exception:
        for storage, name in created_names:
            storage.delete(name)  # type: ignore[attr-defined]
        raise
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
