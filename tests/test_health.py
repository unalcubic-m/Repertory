import pytest
from django.urls import reverse


def test_live_health_has_no_sensitive_detail(client) -> None:
    response = client.get(reverse("health-live"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_ready_health_checks_migrated_database_and_media(client, settings, tmp_path) -> None:
    settings.MEDIA_ROOT = tmp_path / "media"

    response = client.get(reverse("health-ready"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert settings.MEDIA_ROOT.is_dir()
