from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("library/import/", views.import_recording_view, name="import"),
    path("library/recordings/<uuid:public_id>/", views.recording_detail, name="recording-detail"),
    path(
        "library/recordings/<uuid:public_id>/audio/",
        views.recording_audio,
        name="recording-audio",
    ),
    path("library/recordings/<uuid:public_id>/parts/new/", views.add_part, name="add-part"),
    path("library/parts/<uuid:public_id>/edit/", views.edit_part, name="edit-part"),
]
