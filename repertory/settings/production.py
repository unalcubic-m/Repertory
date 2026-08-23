import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required")

DEBUG = False
ALLOWED_HOSTS = ["repertory.metrekare.cloud"]
CSRF_TRUSTED_ORIGINS = ["https://repertory.metrekare.cloud"]

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
