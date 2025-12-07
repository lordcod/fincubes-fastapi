FROM python:3.12-slim

ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_INDEX_URL=https://pypi.org/simple

RUN echo "deb https://mirror.yandex.ru/debian bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb https://mirror.yandex.ru/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb https://mirror.yandex.ru/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc libpq-dev binwalk ca-certificates curl && \
    update-ca-certificates && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel --root-user-action=ignore && \
    python -m pip install "poetry==$POETRY_VERSION" --root-user-action=ignore

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config installer.parallel false \
    && poetry lock --no-update \
    && poetry install --no-root --no-interaction --no-ansi

COPY . .

RUN poetry install --only-root --no-interaction --no-ansi
RUN poetry build -f wheel --no-interaction --no-ansi

EXPOSE 8000
CMD ["poetry", "run", "start"]