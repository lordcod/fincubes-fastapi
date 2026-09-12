FROM python:3.12-slim

ENV POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN python -m pip install --no-cache-dir --disable-pip-version-check \
    "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root --no-interaction --no-ansi

COPY app ./app

EXPOSE 8000
CMD ["python", "-c", "from app.main import start; start()"]
