import os
import subprocess
import sys


def test_production_serves_static_and_trusts_only_https_proxy_signal() -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "DJANGO_SECRET_KEY": "test-only-production-import",
            "RENDER_EXTERNAL_HOSTNAME": "repertory-mvp.onrender.com",
            "REPERTORY_ALLOWED_HOSTS": "music.example.test",
        }
    )
    script = """
from repertory.settings import production

assert production.ALLOWED_HOSTS == [
    "repertory-mvp.onrender.com",
    "music.example.test",
]
assert production.CSRF_TRUSTED_ORIGINS == [
    "https://repertory-mvp.onrender.com",
    "https://music.example.test",
]
assert production.SECURE_PROXY_SSL_HEADER == (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)
assert production.MIDDLEWARE[0:2] == [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]
assert (
    production.STORAGES["staticfiles"]["BACKEND"]
    == "whitenoise.storage.CompressedManifestStaticFilesStorage"
)
"""

    subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
