from .base import *  # noqa: F403

SECRET_KEY = "test-only"
DEBUG = False
ALLOWED_HOSTS = ["testserver"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
DATABASES["default"]["NAME"] = ":memory:"  # noqa: F405
MEDIA_ROOT = BASE_DIR / "var" / "test-media"  # noqa: F405
