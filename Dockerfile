FROM python:3.12-slim

ENV POETRY_VERSION=1.8.2 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

RUN echo "deb https://mirror.yandex.ru/debian bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb https://mirror.yandex.ru/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb https://mirror.yandex.ru/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc libpq-dev binwalk ca-certificates && \
    update-ca-certificates && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install "poetry==$POETRY_VERSION"

WORKDIR /app
COPY . .

RUN poetry lock --no-update
RUN poetry install --no-interaction --no-ansi
RUN poetry build -f wheel --no-interaction --no-ansi

EXPOSE 8000
CMD ["poetry", "run", "start"]
