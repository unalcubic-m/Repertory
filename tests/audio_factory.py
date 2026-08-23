import os
import shutil
import subprocess
from pathlib import Path


def ffmpeg_binary() -> str | None:
    configured = os.environ.get("REPERTORY_TEST_FFMPEG")
    return configured or shutil.which("ffmpeg")


def generate_sine_mp3(path: Path, *, variable_bitrate: bool) -> None:
    binary = ffmpeg_binary()
    if binary is None:
        raise RuntimeError("FFmpeg is not available")
    quality_arguments = ["-q:a", "4"] if variable_bitrate else ["-b:a", "128k"]
    command = [
        binary,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:sample_rate=44100",
        "-t",
        "8",
        "-c:a",
        "libmp3lame",
        *quality_arguments,
        "-metadata",
        "title=Secret synthetic title",
        "-metadata",
        "artist=Secret synthetic artist",
        "-y",
        str(path),
    ]
    subprocess.run(command, check=True, timeout=20)
