from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path("", views.study, name="study"),
    path("<uuid:public_id>/audio/", views.study_audio, name="audio"),
    path("<uuid:public_id>/answer/", views.answer, name="answer"),
    path("<uuid:public_id>/rate/", views.rate, name="rate"),
]
