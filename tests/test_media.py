from pathlib import Path

from library.media import protected_audio_response


def response_body(response) -> bytes:
    if getattr(response, "streaming", False):
        return b"".join(response.streaming_content)
    return response.content


def test_range_response_returns_requested_bytes(tmp_path: Path) -> None:
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"0123456789")

    response = protected_audio_response(path, "bytes=2-5")

    assert response.status_code == 206
    assert response.headers["Content-Range"] == "bytes 2-5/10"
    assert response.headers["Cache-Control"] == "private, no-store, no-transform"
    assert response_body(response) == b"2345"


def test_invalid_range_fails_safely(tmp_path: Path) -> None:
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"0123456789")

    response = protected_audio_response(path, "bytes=20-30")

    assert response.status_code == 416
    assert response.headers["Content-Range"] == "bytes */10"
