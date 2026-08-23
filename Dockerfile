FROM node:24-alpine AS frontend
WORKDIR /app
COPY package.json package-lock.json tsconfig.json ./
COPY frontend ./frontend
RUN npm ci && npm run build

FROM ghcr.io/astral-sh/uv:0.12.5 AS uv

FROM python:3.13-slim-bookworm AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    DJANGO_SETTINGS_MODULE=repertory.settings.production
WORKDIR /app
COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
COPY --from=frontend /app/static/repertory ./static/repertory
RUN DJANGO_SETTINGS_MODULE=repertory.settings.test .venv/bin/python manage.py collectstatic --noinput \
    && mkdir -p /var/lib/repertory/db /var/lib/repertory/media /var/tmp/repertory \
    && chown -R 10001:10001 /var/lib/repertory /var/tmp/repertory
USER 10001:10001
EXPOSE 8000
CMD [".venv/bin/gunicorn", "--bind=0.0.0.0:8000", "--workers=1", "--access-logfile=-", "repertory.wsgi:application"]
