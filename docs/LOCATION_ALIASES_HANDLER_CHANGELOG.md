# Changelog `GET /admin/locations/aliases/` для обработчиков

Дата изменения: 29 июля 2026 года.

## Кратко

Endpoint полного справочника aliases получил контекстные параметры региона и
города. Формат ответа унифицирован: значением каждого ключа alias теперь
**всегда является массив объектов локации**.

```http
GET /admin/locations/aliases/
```

Scope для доступа не изменился: `athlete:read`.

Изменение не требует миграции базы данных.

## Breaking change формата ответа

Раньше однозначный alias возвращал объект:

```json
{
  "КВВС \"Касатка\"": {
    "id": "location-object-id",
    "city": "Томск",
    "region": "Томская область",
    "required": []
  }
}
```

Теперь любой alias возвращает массив, даже если объект только один:

```json
{
  "КВВС \"Касатка\"": [
    {
      "id": "location-object-id",
      "aliases": ["КВВС \"Касатка\""],
      "club": "КВВС \"Касатка\"",
      "club_id": "club-id",
      "city": "Томск",
      "city_id": "tomsk-id",
      "region": "Томская область",
      "region_id": "tomsk-region-id",
      "required": []
    }
  ]
}
```

Тип ответа:

```text
dict[str, list[LocationCatalogItem]]
```

Поля `LocationCatalogItem`:

| Поле | Тип |
|---|---|
| `id` | UUID объекта локации |
| `aliases` | `string[]` |
| `club` | `string \| null` |
| `club_id` | `UUID \| null` |
| `city` | `string \| null` |
| `city_id` | `UUID \| null` |
| `region` | `string` |
| `region_id` | UUID |
| `required` | `("city" \| "region")[]` |

## Новые query-параметры

```http
GET /admin/locations/aliases/?region_id=<uuid>&city_id=<uuid>
```

| Параметр | Тип | Обязательный |
|---|---|---|
| `region_id` | UUID | нет |
| `city_id` | UUID | нет |

Названия региона и города этот endpoint не принимает. Сначала обработчик
получает нормализованные ID через endpoints поиска, затем передаёт ID в
справочник aliases.

## Алгоритм фильтрации

Если `region_id` и `city_id` одновременно отсутствуют, фильтрация не
выполняется: возвращается полный справочник, включая все варианты
неоднозначных aliases.

Если передан хотя бы один параметр, backend проверяет только поля, перечисленные
в `required` конкретного объекта.

| `required` объекта | Условие включения при наличии контекста |
|---|---|
| `[]` | объект включается всегда |
| `["region"]` | `region_id` передан и совпадает |
| `["city"]` | `city_id` передан и совпадает |
| `["city", "region"]` | оба ID переданы и оба совпадают |

Правила:

- отсутствующий обязательный ID считается несовпадением;
- несовпавший обязательный ID исключает объект из ответа;
- переданный, но не указанный в `required` параметр не влияет на объект;
- после исключения всех объектов ключ alias также удаляется из ответа;
- отсутствие подходящего объекта не является ошибкой API.

Эквивалентная логика:

```python
if region_id is None and city_id is None:
    include = True
else:
    include = True
    if "region" in location.required:
        include = include and location.region_id == region_id
    if "city" in location.required:
        include = include and location.city_id == city_id
```

## Пример без контекста

```http
GET /admin/locations/aliases/
```

```json
{
  "СШ ВВС": [
    {
      "id": "perm-location-id",
      "city": "Пермь",
      "city_id": "perm-id",
      "region": "Пермский край",
      "region_id": "perm-region-id",
      "required": ["region"]
    },
    {
      "id": "crimea-location-id",
      "city": "Симферополь",
      "city_id": "simferopol-id",
      "region": "Республика Крым",
      "region_id": "crimea-region-id",
      "required": ["region"]
    }
  ],
  "КВВС \"Касатка\"": [
    {
      "id": "tomsk-location-id",
      "city": "Томск",
      "region": "Томская область",
      "required": []
    }
  ]
}
```

## Пример с регионом

```http
GET /admin/locations/aliases/?region_id=<crimea-region-id>
```

```json
{
  "СШ ВВС": [
    {
      "id": "crimea-location-id",
      "city": "Симферополь",
      "city_id": "simferopol-id",
      "region": "Республика Крым",
      "region_id": "crimea-region-id",
      "required": ["region"]
    }
  ],
  "КВВС \"Касатка\"": [
    {
      "id": "tomsk-location-id",
      "city": "Томск",
      "region": "Томская область",
      "required": []
    }
  ]
}
```

`КВВС "Касатка"` остаётся в ответе, потому что у объекта пустой `required`.

Если передать только `city_id`, варианты `СШ ВВС` будут исключены: для них
обязателен `region_id`.

## Рекомендуемый алгоритм обработчика

1. Получить исходные `alias`, город и регион из результата.
2. Найти регион:

   ```http
   GET /admin/locations/regions/?query=<region>
   ```

3. При наличии города найти его с контекстом региона:

   ```http
   GET /admin/locations/cities/?query=<city>&region_id=<region-id>
   ```

4. Получить справочник с найденными ID:

   ```http
   GET /admin/locations/aliases/?region_id=<region-id>&city_id=<city-id>
   ```

5. Взять массив по точному исходному ключу:

   ```python
   candidates = catalog.get(source_alias, [])
   ```

6. Обработать результат:

   - один объект — использовать его `id`;
   - несколько объектов — контекста недостаточно, требуется дополнительное
     уточнение;
   - пустой массив или отсутствующий ключ — совместимый объект не найден.

7. Если нужный объект уже существует, но исходного alias ещё нет в его
   `aliases`, добавить alias отдельным endpoint:

   ```http
   POST /admin/locations/aliases/{location_id}/aliases/
   ```

   ```json
   {
     "aliases": [
       "новое исходное название команды"
     ]
   }
   ```

8. При создании атлета передать ID выбранного объекта и исходный alias:

   ```json
   {
     "location": {
       "location_id": "selected-location-id",
       "alias": "исходное название команды"
     }
   }
   ```

## Добавление aliases существующему объекту

```http
POST /admin/locations/aliases/{location_id}/aliases/
```

Scope: `athlete:create`.

Этот endpoint используется, когда клуб, город, регион и сам
`LocationObject` уже существуют. Он не создаёт новый объект и не изменяет его
клуб, город или регион — только дополняет массив `aliases`.

Тело запроса:

```json
{
  "aliases": [
    "Новое название",
    "Другой вариант написания"
  ]
}
```

Ответ: обновлённый `LocationObject`.

Операция идемпотентна:

- alias, уже находящийся в этом объекте, повторно не добавляется;
- остальные aliases добавляются с сохранением исходного написания;
- порядок уже существующих aliases сохраняется.

Один alias можно добавить к нескольким объектам только тогда, когда:

- объекты относятся к разным регионам;
- у обоих объектов `required` содержит `region`.

В остальных случаях endpoint возвращает
`3021 LOCATION_ALIAS_CONFLICT`.

Если `location_id` не существует, возвращается:

```text
3024 LOCATION_OBJECT_NOT_FOUND
```

Пример полного решения обработчика:

```text
нормализованные club/city/region найдены
             |
             v
существующий LocationObject найден?
        |                    |
       да                   нет
        |                    |
        v                    v
добавить исходный alias    POST /admin/locations/aliases/
через POST .../{id}/       создать новый LocationObject
aliases/
        |                    |
        +---------+----------+
                  |
                  v
создать атлета с location_id и исходным alias
```

## Что важно изменить в клиенте

- Удалить разбор типа `object | array`: теперь значение всегда массив.
- Не выбирать первый элемент без проверки длины массива.
- Для кэша полного справочника учитывать `region_id` и `city_id` в ключе.
- Не считать отсутствие alias в отфильтрованном ответе ошибкой endpoint.
- Не передавать названия в `region_id` и `city_id`: параметры принимают UUID.

Пример типа TypeScript:

```typescript
type LocationCatalog = Record<string, LocationCatalogItem[]>;
```

## Ошибки

Endpoint не возвращает бизнес-ошибку при несовпадении `required`: неподходящие
объекты просто исключаются.

- некорректный формат UUID — стандартная ошибка валидации `422`;
- отсутствие авторизации — `401`;
- отсутствие scope `athlete:read` — `403`.

Для endpoint добавления aliases требуется scope `athlete:create`. Его
дополнительные ошибки:

- `3024 LOCATION_OBJECT_NOT_FOUND` — переданного `location_id` нет;
- `3021 LOCATION_ALIAS_CONFLICT` — alias уже принадлежит несовместимому
  объекту;
- `422` — пустой список, пустой alias, дубликаты в теле запроса или alias
  длиннее 512 символов.

Поведение точного endpoint не изменилось:

```http
GET /admin/locations/aliases/resolve?alias=<alias>&region_id=<uuid>
```

Если один alias относится к нескольким регионам и `region_id` не передан,
`/resolve` возвращает `3019 LOCATION_REGION_REQUIRED`.

## Проверка реализации

- response model в OpenAPI:
  `dict[str, list[LocationCatalogItem]]`;
- query-параметры в OpenAPI: `region_id`, `city_id`;
- автоматические тесты проверяют полный ответ, фильтрацию по региону,
  отсутствие обязательного параметра и объекты с пустым `required`.
