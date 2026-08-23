import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required")

DEBUG = False


def _environment_list(name: str) -> list[str]:
    return [value.strip() for value in os.environ.get(name, "").split(",") if value.strip()]


_render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
ALLOWED_HOSTS = list(
    dict.fromkeys(
        [
            value
            for value in [_render_hostname, *_environment_list("REPERTORY_ALLOWED_HOSTS")]
            if value
        ]
    )
)
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("RENDER_EXTERNAL_HOSTNAME or REPERTORY_ALLOWED_HOSTS is required")

CSRF_TRUSTED_ORIGINS = list(
    dict.fromkeys(
        [
            *(f"https://{host}" for host in ALLOWED_HOSTS),
            *_environment_list("REPERTORY_CSRF_TRUSTED_ORIGINS"),
        ]
    )
)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

MIDDLEWARE = [
    MIDDLEWARE[0],  # noqa: F405
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],  # noqa: F405
]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

DATABASES["default"]["NAME"] = Path(  # noqa: F405
    os.environ.get("REPERTORY_DATABASE", "/var/lib/repertory/db/repertory.sqlite3")
)
MEDIA_ROOT = Path(os.environ.get("REPERTORY_MEDIA_ROOT", "/var/lib/repertory/media"))
