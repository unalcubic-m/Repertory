from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from mutagen.mp3 import MP3

from library.audio import import_recording
from tests.audio_factory import ffmpeg_binary, generate_sine_mp3


@pytest.mark.parametrize("variable_bitrate", [False, True], ids=["cbr", "vbr"])
@pytest.mark.django_db
def test_real_synthetic_mp3_import_strips_identifying_tags(
    owner, settings, tmp_path: Path, variable_bitrate: bool
) -> None:
    if ffmpeg_binary() is None:
        pytest.skip("FFmpeg is unavailable")
    settings.MEDIA_ROOT = tmp_path / "media"
    source = tmp_path / "synthetic.mp3"
    generate_sine_mp3(source, variable_bitrate=variable_bitrate)
    tagged = MP3(source)
    assert tagged.tags is not None
    assert "TIT2" in tagged.tags

    upload = SimpleUploadedFile("Synthetic Work.mp3", source.read_bytes(), "audio/mpeg")
    recording = import_recording(
        owner=owner,
        composer_name="Synthetic Composer",
        work_title="Synthetic Work",
        recording_label="Generated test recording",
        upload=upload,
    )

    preserved = MP3(recording.original_file.path)
    playback = MP3(recording.playback_file.path)
    assert preserved.tags is not None and "TIT2" in preserved.tags
    assert playback.tags is None or "TIT2" not in playback.tags
    assert 7_500 <= recording.duration_ms <= 8_500
