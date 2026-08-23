#!/bin/sh
set -eu

.venv/bin/python manage.py migrate --noinput

exec .venv/bin/gunicorn \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --access-logfile - \
    --timeout 120 \
    repertory.wsgi:application
