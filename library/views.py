from pathlib import Path
from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from reviews.models import StudyState

from .forms import PartForm, RecordingImportForm, format_timecode
from .media import protected_audio_response
from .models import Part, Recording


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    owner = cast(User, request.user)
    recordings = (
        Recording.objects.filter(owner=owner, archived=False)
        .select_related("work", "work__composer")
        .annotate(part_count=Count("parts", filter=Q(parts__archived=False)))
    )
    due_count = StudyState.objects.filter(
        owner=owner,
        part__archived=False,
        part__recording__archived=False,
        due_at__lte=timezone.now(),
    ).count()
    return render(
        request,
        "library/dashboard.html",
        {"recordings": recordings, "due_count": due_count},
    )


@login_required
def import_recording_view(request: HttpRequest) -> HttpResponse:
    owner = cast(User, request.user)
    form = RecordingImportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            recording = form.save(owner)
        except ValidationError as error:
            form.add_error("audio_file", error)
        else:
            messages.success(
                request, "MP3 imported. Mark the movement or section you want to study."
            )
            return redirect("library:recording-detail", public_id=recording.public_id)
    return render(request, "library/import.html", {"form": form})


@login_required
def recording_detail(request: HttpRequest, public_id: str) -> HttpResponse:
    owner = cast(User, request.user)
    recording = get_object_or_404(
        Recording.objects.select_related("work", "work__composer").prefetch_related(
            "parts__aliases"
        ),
        owner=owner,
        public_id=public_id,
    )
    return render(
        request,
        "library/recording_detail.html",
        {
            "recording": recording,
            "duration": format_timecode(recording.duration_ms),
        },
    )


@login_required
def recording_audio(request: HttpRequest, public_id: str) -> HttpResponseBase:
    owner = cast(User, request.user)
    recording = get_object_or_404(
        Recording,
        owner=owner,
        public_id=public_id,
        status=Recording.Status.READY,
    )
    path = Path(recording.playback_file.path)
    if not path.is_file():
        return HttpResponse(status=404)
    return protected_audio_response(path, request.headers.get("Range"))


@login_required
def add_part(request: HttpRequest, public_id: str) -> HttpResponse:
    owner = cast(User, request.user)
    recording = get_object_or_404(
        Recording,
        owner=owner,
        public_id=public_id,
        archived=False,
    )
    form = PartForm(request.POST or None, recording=recording)
    if request.method == "POST" and form.is_valid():
        form.save(owner)
        messages.success(request, "Study part added. It is ready for review.")
        return redirect("library:recording-detail", public_id=recording.public_id)
    return render(request, "library/part_form.html", {"form": form, "recording": recording})


@login_required
def edit_part(request: HttpRequest, public_id: str) -> HttpResponse:
    owner = cast(User, request.user)
    part = get_object_or_404(
        Part.objects.select_related("recording", "recording__work").prefetch_related("aliases"),
        owner=owner,
        public_id=public_id,
        archived=False,
    )
    form = PartForm(request.POST or None, recording=part.recording, instance=part)
    if request.method == "POST" and form.is_valid():
        form.save(owner)
        messages.success(request, "Study part updated.")
        return redirect("library:recording-detail", public_id=part.recording.public_id)
    return render(
        request,
        "library/part_form.html",
        {"form": form, "recording": part.recording, "part": part},
    )
