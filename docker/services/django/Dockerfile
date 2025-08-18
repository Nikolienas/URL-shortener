FROM python:3.12-alpine

ENV WORKDIR=/app
WORKDIR $WORKDIR

RUN adduser -D -s /bin/bash admin

RUN apk update && \
    apk add --no-cache \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    cairo \
    cairo-dev \
    pkgconfig

RUN pip install --upgrade pip
RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false
RUN poetry install --no-root

RUN mkdir -p $WORKDIR/static $WORKDIR/media && \
    chown -R admin:admin $WORKDIR/static $WORKDIR/media

USER admin

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
