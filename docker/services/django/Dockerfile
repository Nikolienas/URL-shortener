FROM python:3.12-alpine

ENV WORKDIR=/app
WORKDIR $WORKDIR

RUN apk update && \
    apk add --no-cache \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    cairo \
    cairo-dev \
    pkgconfig

RUN pip install --upgrade pip && \
    pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-root

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1