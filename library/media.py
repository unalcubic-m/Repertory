import re
from collections.abc import Iterator
from pathlib import Path

from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.http.response import HttpResponseBase

RANGE_PATTERN = re.compile(r"^bytes=(\d*)-(\d*)$")
CHUNK_SIZE = 64 * 1024


def _iter_range(path: Path, start: int, length: int) -> Iterator[bytes]:
    with path.open("rb") as handle:
        handle.seek(start)
        remaining = length
        while remaining:
            data = handle.read(min(CHUNK_SIZE, remaining))
            if not data:
                break
            remaining -= len(data)
            yield data


def _set_headers(response: HttpResponseBase, headers: dict[str, str]) -> None:
    for name, value in headers.items():
        response.headers[name] = value


def protected_audio_response(path: Path, range_header: str | None) -> HttpResponseBase:
    size = path.stat().st_size
    common_headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "private, no-store, no-transform",
        "Content-Type": "audio/mpeg",
        "Content-Disposition": 'inline; filename="audio.mp3"',
        "X-Content-Type-Options": "nosniff",
    }
    if not range_header:
        full_response = FileResponse(path.open("rb"), content_type="audio/mpeg")
        _set_headers(full_response, common_headers)
        full_response.headers["Content-Length"] = str(size)
        return full_response

    match = RANGE_PATTERN.fullmatch(range_header.strip())
    if match is None or "," in range_header:
        error_response = HttpResponse(status=416)
        error_response.headers["Content-Range"] = f"bytes */{size}"
        return error_response
    start_text, end_text = match.groups()
    if not start_text and not end_text:
        error_response = HttpResponse(status=416)
        error_response.headers["Content-Range"] = f"bytes */{size}"
        return error_response
    if start_text:
        start = int(start_text)
        end = int(end_text) if end_text else size - 1
    else:
        suffix_length = int(end_text)
        if suffix_length <= 0:
            error_response = HttpResponse(status=416)
            error_response.headers["Content-Range"] = f"bytes */{size}"
            return error_response
        start = max(0, size - suffix_length)
        end = size - 1
    if start >= size or end < start:
        error_response = HttpResponse(status=416)
        error_response.headers["Content-Range"] = f"bytes */{size}"
        return error_response
    end = min(end, size - 1)
    length = end - start + 1
    range_response = StreamingHttpResponse(
        _iter_range(path, start, length), status=206, content_type="audio/mpeg"
    )
    _set_headers(range_response, common_headers)
    range_response.headers["Content-Length"] = str(length)
    range_response.headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    return range_response
