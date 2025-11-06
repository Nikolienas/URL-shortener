FROM python:3.12-alpine

ENV WORKDIR=/app
WORKDIR $WORKDIR

RUN pip install --upgrade pip && \
    pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-root

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["python", "manage.py", "start_bot"]