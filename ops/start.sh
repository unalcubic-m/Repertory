#!/bin/sh
set -eu

if [ "$(id -u)" = "0" ]; then
    mkdir -p /var/lib/repertory/db /var/lib/repertory/media /var/tmp/repertory
    chown 10001:10001 \
        /var/lib/repertory \
        /var/lib/repertory/db \
        /var/lib/repertory/media \
        /var/tmp/repertory
    exec gosu repertory:repertory "$0" "$@"
fi

.venv/bin/python manage.py migrate --noinput

exec .venv/bin/gunicorn \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --access-logfile - \
    --timeout 120 \
    repertory.wsgi:application
