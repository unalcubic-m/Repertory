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
RUN apt-get update \
    && apt-get install --yes --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 repertory \
    && useradd --uid 10001 --gid 10001 --home-dir /app --no-create-home --shell /bin/sh repertory
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
COPY --from=frontend /app/static/repertory ./static/repertory
RUN DJANGO_SECRET_KEY=build-only-not-used-at-runtime \
    REPERTORY_ALLOWED_HOSTS=build.invalid \
    .venv/bin/python manage.py collectstatic --noinput \
    && mkdir -p /var/lib/repertory/db /var/lib/repertory/media /var/tmp/repertory \
    && chown -R 10001:10001 /var/lib/repertory /var/tmp/repertory
EXPOSE 8000
CMD ["./ops/start.sh"]
