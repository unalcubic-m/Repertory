from pathlib import Path

from .base import *  # noqa: F403

SECRET_KEY = "development-only-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

Path(str(DATABASES["default"]["NAME"])).parent.mkdir(parents=True, exist_ok=True)  # noqa: F405
Path(MEDIA_ROOT).mkdir(parents=True, exist_ok=True)  # noqa: F405
