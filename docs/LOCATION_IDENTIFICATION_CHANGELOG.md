# Нормализация локаций и идентификация атлетов

> Актуальный формат `GET /admin/locations/aliases/`, включая массивы значений
> и фильтрацию по `region_id`/`city_id`, описан в
> [LOCATION_CATALOG_ADDITIONS.md](LOCATION_CATALOG_ADDITIONS.md) и заменяет
> первоначальный пример формата ниже.

## Что изменилось в backend

Добавлены две таблицы:

- `location_objects` — денормализованный справочник. Одна строка содержит
  список `aliases`, `club/club_id`, `city/city_id`, `region/region_id` и
  `required`. Несколько исходных ключей одного объекта находятся в одном
  списке `aliases`.
- `locations` — связь атлета с объектом справочника. Сохраняет `athlete_id`,
  `location_object_id` и конкретный исходный `alias`, по которому атлет был
  связан.

Связь множественная: у одного атлета может быть несколько записей `locations`.
Понятия «текущая локация» пока нет.

Существующие `athletes.club` и `athletes.city` не удалены. Это переходные поля,
которые сохраняют совместимость старого frontend и старых импортов.

Старый review-workflow полностью удалён: больше нет моделей и таблиц
`ReviewDecision`, `ReviewItem`, `ReviewSession`, review-enum’ов и endpoints
`resolve-candidates`, `resolve-preview`, `review-sessions`. Миграция 12 удаляет
эти таблицы, если они были созданы ранее.

## Порядок развёртывания

1. Применить миграцию `12_20260729110000_location_catalog.py`.
2. Заполнить справочник:

   ```powershell
   .\.venv\Scripts\python.exe scripts/import_location_catalog.py --dry-run
   .\.venv\Scripts\python.exe scripts/import_location_catalog.py
   ```

3. Проверить перенос существующих атлетов:

   ```powershell
   .\.venv\Scripts\python.exe scripts/migrate_athlete_locations.py --dry-run
   ```

4. Выполнить перенос и получить файл несовпадений:

   ```powershell
   .\.venv\Scripts\python.exe scripts/migrate_athlete_locations.py `
     --output athlete-location-unmatched.json
   ```

Оба скрипта идемпотентны. Для ненайденных алиасов связь не создаётся — они
попадают в JSON-выгрузку для последующего дополнения справочника.

## API справочника

Все методы используют существующие scopes:

- чтение и поиск — `athlete:read`;
- создание нового алиаса — `athlete:create`.

### Полный JSON

`GET /admin/locations/aliases/`

Ответ сохраняет исходный формат «alias как ключ»:

```json
{
  "СК \"Айсберг\" г. Саратов": {
    "id": "7d537d8e-8315-4f5c-99b6-45716d6eb324",
    "aliases": [
      "СК \"Айсберг\" г. Саратов"
    ],
    "club": "СК \"Айсберг\"",
    "club_id": "58437be9-c431-52ed-b731-d0befbaf04c3",
    "city": "Саратов",
    "city_id": "f28fc923-0368-5b9c-b75c-c4940b7a2f9d",
    "region": "Саратовская область",
    "region_id": "d79e5785-8486-5c59-9d37-df27f73a759f",
    "required": []
  }
}
```

Поле `id` — детерминированный UUID5 нормализованного объекта, вычисленный из
`club_id + city_id + region_id`. Все ключи из `aliases` возвращают один и тот
же объект и один `id`. UUID в примере условный: фактический ID возвращает API.

### Точное разрешение alias

`GET /admin/locations/aliases/resolve?alias=...`

Сначала выполняется точное сравнение исходного ключа без изменения регистра
или пробелов. Это важно, потому что нормализованно одинаковые ключи иногда
ведут на разные объекты. Неточное разрешение выполняется через `/search`.

### Поиск с подсказками

- `GET /admin/locations/regions/?query=масква&limit=10`
- `GET /admin/locations/cities/?query=симферопол&region_id=<uuid>`
- `GET /admin/locations/clubs/?query=айсберк&region_id=<uuid>&city_id=<uuid>`
- `GET /admin/locations/aliases/search?query=айсберк&region_id=<uuid>&city_id=<uuid>`

Каждый вариант возвращает:

```json
[
  {
    "id": "62f953a6-21be-5b0a-99b2-47698fd60bfe",
    "name": "Москва",
    "exact_match": false,
    "similarity": 0.833333
  }
]
```

Точное совпадение всегда сортируется первым и отмечается
`exact_match: true`. При опечатке возвращаются приблизительные варианты.

### Создание или дополнение объекта

`POST /admin/locations/aliases/`

```json
{
  "aliases": [
    "Новая команда г. Новый город",
    "Новая команда"
  ],
  "club": "Новая команда",
  "city": "Новый город",
  "region": "Новый регион",
  "required": ["city", "region"]
}
```

`region` обязателен. Если `club_id`, `city_id` или `region_id` не переданы,
backend сначала ищет точное совпадение названия. Для новой сущности создаётся
детерминированный UUID5. Если объект с такой комбинацией ID уже существует,
новые значения дополняют его `aliases`. Один alias не может принадлежать двум
разным объектам.

## Создание атлета

Обычное и bulk-создание принимают необязательный объект `location`:

```json
{
  "last_name": "Иванов",
  "first_name": "Иван",
  "birth_year": 2010,
  "gender": "M",
  "location": {
    "location_id": "7d537d8e-8315-4f5c-99b6-45716d6eb324",
    "alias": "СК \"Айсберг\" г. Саратов"
  }
}
```

Backend проверяет, что `alias` действительно принадлежит переданному
`location_id`, и атомарно создаёт атлета вместе со связью. Для старых
клиентов поля `club/city` продолжают приниматься. Если они не переданы,
переходные значения заполняются из нормализованной локации.

Связи атлета можно прочитать отдельно:

`GET /admin/locations/athletes/{athlete_id}/`

## Изменения для frontend/обработчика

1. Перед созданием атлета разрешить исходную команду через
   `/aliases/resolve`; если точного alias нет — показать подсказки поиска.
2. Если подходящего объекта нет, создать его через `POST /aliases/`.
3. При создании атлета передавать `location.location_id` и исходный
   `location.alias`.
4. Для нового интерфейса отображения клуба брать нормализованные данные из
   `GET /admin/locations/athletes/{athlete_id}/`.
5. `athlete.club` и `athlete.city` пока можно использовать как fallback, но
   новые функции не должны считать их источником нормализованных ID.

## Новые ошибки

- `3019 LOCATION_REGION_REQUIRED` — регион не указан;
- `3020 LOCATION_ALIAS_NOT_FOUND` — объект alias не найден;
- `3021 LOCATION_ALIAS_CONFLICT` — alias уже существует;
- `3022 LOCATION_ALIAS_MISMATCH` — alias не принадлежит переданному ID;
- `3023 LOCATION_ENTITY_ID_CONFLICT` — название уже связано с другим ID.

Формат ошибки остаётся прежним: `error_code`, `error_name`, `message`.
