# fincubes-fastapi

Backend на FastAPI для проекта [fincubes.ru](https://fincubes.ru), реализующий полную бизнес-логику, включая аутентификацию, авторизацию, работу с базой данных и хранение файлов.

## Описание

Это полноценный backend-сервис, построенный с использованием FastAPI и Tortoise ORM, обеспечивающий:

- Многоуровневую аутентификацию и авторизацию с кастомной системой scopes
- Защиту публичных методов API собственной системой безопасности
- Использование FastFSX для эффективной работы с файловым хранилищем
- Генерацию новых scope при обновлении (refresh) токена
- Гибкую систему зависимостей (dependencies) для авторизации
- Хранение файлов в облачном хранилище (например, Yandex.Cloud)

## Ключевые возможности

- Собственная система защиты публичных методов и scope-based авторизация
- Многоуровневая авторизация с поддержкой обновления прав в refresh-токенах
- Интеграция с Cloudflare Turnstile для проверки пользователей при login/signup
- Готовые механизмы работы с SMTP для отправки почты
- Поддержка PostgreSQL с оптимизациями для этого СУБД
- Возможность развертывания через Poetry, Docker и Docker Compose

## Требования к окружению

Для корректной работы нужно настроить `.env` с параметрами:

```env
SECRET_KEY=""           # JWT секретный ключ
TURNSTILE_SECRET_KEY="" # Cloudflare Turnstile secret key
SMTP_HOST=""
SMTP_PORT=""
SMTP_USER=""
SMTP_PASSWORD=""
AWS_KEY_ID=""           # Ключ для облачного хранилища (например, Yandex.Cloud)
AWS_SECRET_KEY=""
BUCKET_NAME=""
REDIS_URL=""            # Redis URL (требуется при использовании Docker/Poetry)
DATABASE_URL=""         # Рекомендуется PostgreSQL
````

## Установка и запуск

### Через Poetry

```bash
poetry install
cp .env.example .env
# заполните .env
poetry run uvicorn app.main:app --reload
```

### Через Docker

```bash
docker build -t fincubes-fastapi .
docker run --env-file .env -p 8000:8000 fincubes-fastapi
```

### Через Docker Compose

```bash
docker-compose up --build
```

## Документация API

Автоматически генерируемая документация доступна по адресу:
[https://api.fincubes.ru/docs](https://api.fincubes.ru/docs)

\[Dybfuo Projects]


Если нужно — помогу сделать более глубокую инструкцию по развёртыванию или тестированию.
