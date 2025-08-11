FROM python:3.12-alpine

WORKDIR /app
RUN mkdir -p $WORKDIR/static
RUN mkdir -p $WORKDIR/media

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

RUN pip install --upgrade pip
RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false
RUN poetry install --no-root

COPY . .