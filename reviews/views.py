from pathlib import Path
from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404, HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from library.media import protected_audio_response

from .forms import AnswerForm, RatingForm
from .models import ReviewSession
from .services import get_or_create_session, rate_answer, reveal_answer


@never_cache
@login_required
def study(request: HttpRequest) -> HttpResponse:
    owner = cast(User, request.user)
    session = get_or_create_session(owner)
    context: dict[str, object] = {"session": session}
    if session is not None:
        context["answer_form"] = AnswerForm(initial={"replay_count": session.replay_count})
        context["rating_form"] = RatingForm()
        context["excerpt_start_seconds"] = session.excerpt_start_ms / 1000
        context["excerpt_end_seconds"] = (
            session.excerpt_start_ms + session.excerpt_duration_ms
        ) / 1000
    return render(request, "reviews/study.html", context)


@never_cache
@login_required
def study_audio(request: HttpRequest, public_id: str) -> HttpResponseBase:
    owner = cast(User, request.user)
    session = get_object_or_404(
        ReviewSession.objects.select_related("part__recording"),
        owner=owner,
        public_id=public_id,
        stage__in=[ReviewSession.Stage.QUESTION, ReviewSession.Stage.REVEALED],
    )
    if session.expires_at <= timezone.now():
        raise Http404
    path = Path(session.part.recording.playback_file.path)
    if not path.is_file():
        raise Http404
    return protected_audio_response(path, request.headers.get("Range"))


@require_POST
@login_required
def answer(request: HttpRequest, public_id: str) -> HttpResponse:
    owner = cast(User, request.user)
    form = AnswerForm(request.POST)
    if form.is_valid():
        try:
            reveal_answer(
                owner=owner,
                session_id=public_id,
                submitted_answer=form.cleaned_data["answer"],
                replay_count=form.cleaned_data["replay_count"],
            )
        except (ReviewSession.DoesNotExist, ValueError):
            messages.error(request, "That review expired or is no longer available.")
    else:
        messages.error(request, "Enter an answer before revealing the result.")
    return redirect("reviews:study")


@require_POST
@login_required
def rate(request: HttpRequest, public_id: str) -> HttpResponse:
    owner = cast(User, request.user)
    form = RatingForm(request.POST)
    if form.is_valid():
        try:
            rate_answer(owner=owner, session_id=public_id, rating=form.cleaned_data["rating"])
        except (ReviewSession.DoesNotExist, ValueError):
            messages.error(request, "That review expired or has already been completed.")
    else:
        messages.error(request, "Choose Again, Hard, Good, or Easy.")
    return redirect("reviews:study")
