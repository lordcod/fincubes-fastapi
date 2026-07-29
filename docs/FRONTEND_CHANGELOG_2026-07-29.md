# Frontend changelog — 29 июля 2026

Документ описывает изменения API, которые влияют на frontend и
сгенерированный Hasura/OpenAPI-клиент.

## Что frontend должен изменить обязательно

1. Перегенерировать API-типы и методы.
2. Обрабатывать `event_type: "INDIVIDUAL" | "RELAY"` во всех результатах.
3. Обновить отображение
   `getAthleteResultsPublicServerAthleteIdPerformancesGet`.
4. Обновить отображение
   `getAthleteTopPublicServerAthleteIdTopGet`.
5. В справочнике aliases всегда ожидать массив объектов, а не
   `object | array`.
6. Удалить старый UI и вызовы review-flow.
7. Для дистанций использовать `relay_count` и `total_distance`.

---

## `getAthleteResultsPublicServerAthleteIdPerformancesGet`

HTTP:

```http
GET /public/server/athlete/{id}/performances/
```

Scope: `athlete.results:read`.

Верхний уровень ответа не изменился:

```ts
interface AthleteResults {
  id: number;
  results: Array<{
    competition: Competition;
    performances: UserPerformance[];
  }>;
}
```

`results` по-прежнему сгруппирован по соревнованиям, а соревнования
отсортированы от новых к старым.

### Новый тип `UserPerformance`

```ts
type EventType = "INDIVIDUAL" | "RELAY";

interface UserPerformance {
  created_at: string;
  updated_at: string;
  id: number;

  event_type: EventType;
  stroke: string;

  /** Длина одной индивидуальной дистанции или одного этапа эстафеты. */
  distance: number;

  /** 1 для индивидуального результата, количество этапов для эстафеты. */
  relay_count: number;

  /** distance * relay_count */
  total_distance: number;

  result: string | null;
  final: string | null;
  resolved_time: string | null;
  place: string | null;
  final_rank: string | null;
  points: string | null;
  record: string | null;
  status: string | null;
  metadata: Record<string, unknown> | unknown[] | null;

  best: boolean;

  /** Заполняется только для RELAY. */
  name: string | null;

  /** Время этапа конкретного атлета. Только для RELAY. */
  split_result: string | null;

  /** Номер этапа атлета. Только для RELAY. */
  relay_order: number | null;

  /** ID RelayLeg. Только для RELAY. */
  relay_leg_id: number | null;

  /** Metadata конкретного этапа. Только для RELAY. */
  leg_metadata: Record<string, unknown> | unknown[] | null;
}
```

### Индивидуальный результат

```json
{
  "id": 501,
  "event_type": "INDIVIDUAL",
  "stroke": "SURFACE",
  "distance": 100,
  "relay_count": 1,
  "total_distance": 100,
  "result": "00:45,20",
  "split_result": null,
  "name": null,
  "relay_order": null,
  "relay_leg_id": null,
  "leg_metadata": null,
  "best": true
}
```

Для `INDIVIDUAL` поведение старых полей `result`, `final`,
`resolved_time`, `place`, `points` и `best` не изменилось.

### Эстафетный результат атлета

```json
{
  "id": 701,
  "event_type": "RELAY",
  "stroke": "SURFACE",
  "distance": 50,
  "relay_count": 4,
  "total_distance": 200,
  "name": "СШ ВВС",
  "result": "01:40,30",
  "split_result": "00:24,10",
  "relay_order": 1,
  "relay_leg_id": 9001,
  "place": "1",
  "points": "50",
  "status": "COMPLETED",
  "best": false
}
```

Семантика полей для `RELAY`:

| Поле | Значение |
|---|---|
| `id` | `RelayResult.id`, общий ID результата команды |
| `name` | буквальное название команды |
| `result` | итоговое время всей команды |
| `split_result` | время этапа текущего атлета |
| `relay_order` | номер этапа текущего атлета |
| `relay_leg_id` | ID записи этапа |
| `distance` | длина одного этапа |
| `relay_count` | количество этапов |
| `total_distance` | полная дистанция эстафеты |
| `place`, `points`, `status` | данные команды |
| `best` | всегда `false` для relay-записи в этом endpoint |

Рекомендуемое отображение:

```ts
if (performance.event_type === "RELAY") {
  // Основное личное значение спортсмена.
  const athleteTime = performance.split_result;

  // Дополнительная информация о команде.
  const teamTime = performance.result;
  const eventLabel =
    `${performance.relay_count} × ${performance.distance}`;
}
```

Не следует показывать `result` как личное время атлета для `RELAY`:
это командный результат.

### Кэш

Кэш используется только внутри этого performance endpoint. TTL — 15 минут.
После появления нового результата старый ответ может сохраняться до
истечения TTL.

---

## `getAthleteTopPublicServerAthleteIdTopGet`

HTTP:

```http
GET /public/server/athlete/{id}/top/
```

Scope: `athlete.results:read`.

Форма верхнего уровня:

```ts
type AthleteTopResponse = Record<string, BestFullResult[]>;

interface BestFullResult {
  result: TopResult;
  athlete: Athlete;
  competition: Competition;
  row_num: number;
}
```

Ключ имеет формат:

```text
current_season:<category>
global:<category>
```

Примеры:

```text
current_season:kids
current_season:junior
global:absolute
```

Если рейтинг для атлета ещё не рассчитан, endpoint возвращает:

```json
{}
```

### Новое поле `result.event_type`

```ts
interface TopResult {
  id: number;
  event_type: "INDIVIDUAL" | "RELAY";
  stroke: string;
  distance: number;
  result: string | null;
  final: string | null;
  resolved_time: string | null;
  place: string | null;
  points: string | null;
  status: string | null;
  metadata: Record<string, unknown> | unknown[] | null;
}
```

### Как relay попадает в рейтинг

Эстафетный результат учитывается только если:

- атлет стоит на первом этапе: `RelayLeg.order === 1`;
- время первого этапа заполнено.

Для такой записи:

```json
{
  "result": {
    "id": 9001,
    "event_type": "RELAY",
    "stroke": "SURFACE",
    "distance": 50,
    "result": "00:24,10",
    "resolved_time": "00:24,10",
    "status": "COMPLETED"
  },
  "row_num": 3
}
```

Критически важно:

- `result.result` здесь — время первого этапа, а не время команды;
- `result.resolved_time` равно времени первого этапа;
- `result.id` для `RELAY` — `RelayLeg.id`;
- `distance` — длина одного этапа;
- `place`, `points` и `status` относятся к команде;
- `metadata` относится к первому этапу;
- этапы `2..relay_count` в рейтинг не попадают;
- командное время в top-response не передаётся.

В top-response также нет `name`, `relay_count`, `total_distance` и
`relay_result_id`. Для места в рейтинге следует использовать `row_num`, а
не командное поле `result.place`.

Первый этап сравнивается с индивидуальными результатами по одной и той же
комбинации:

```text
stroke + distance + gender
```

В `row_num` уже находится готовое место в рейтинге. Frontend не должен
пересчитывать место самостоятельно.

### Материализация рейтинга

Этот endpoint читает заранее рассчитанный рейтинг из MongoDB. Данные
обновляются ежедневной задачей либо ручным rebuild, поэтому relay-результат
может появиться в `performances` раньше, чем в `top`.

---

## Общий `event_type` в результатах

В ответы обычных `Result` добавлено:

```json
{
  "event_type": "INDIVIDUAL"
}
```

В ответы `RelayResult` добавлено:

```json
{
  "event_type": "RELAY"
}
```

`event_type` не передаётся при создании. Его назначает backend в зависимости
от endpoint:

- `/admin/result/...` → `INDIVIDUAL`;
- `/admin/relay-results/...` → `RELAY`.

Frontend должен использовать исчерпывающую проверку:

```ts
switch (result.event_type) {
  case "INDIVIDUAL":
    break;
  case "RELAY":
    break;
}
```

---

## Дистанции

В `Distance` добавлены:

```ts
interface Distance {
  distance: number;
  relay_count: number;
  total_distance: number;
}
```

Семантика:

- индивидуальные `100 м`: `distance=100`, `relay_count=1`,
  `total_distance=100`;
- эстафета `4 × 50 м`: `distance=50`, `relay_count=4`,
  `total_distance=200`.

`relay_count` по умолчанию равен `1`. `total_distance` вычисляется backend и
не передаётся при создании.

Для подписи дистанции:

```ts
const label =
  distance.relay_count > 1
    ? `${distance.relay_count} × ${distance.distance} м`
    : `${distance.distance} м`;
```

---

## Новые relay endpoints

### Создание

```http
POST /admin/relay-results/
```

```json
{
  "competition_id": 123,
  "name": "СШ ВВС",
  "stroke": "SURFACE",
  "distance": 50,
  "relay_count": 4,
  "gender": "M",
  "result": "01:40.30",
  "place": "1",
  "points": "50",
  "status": "COMPLETED",
  "metadata": null,
  "legs": [
    {
      "athlete_id": 101,
      "order": 1,
      "result": "00:24.10",
      "metadata": null
    },
    {
      "athlete_id": 102,
      "order": 2,
      "result": "00:25.20",
      "metadata": null
    },
    {
      "athlete_id": 103,
      "order": 3,
      "result": "00:24.80",
      "metadata": null
    },
    {
      "athlete_id": 104,
      "order": 4,
      "result": "00:26.20",
      "metadata": null
    }
  ]
}
```

В реальном запросе количество `legs` должно быть равно `relay_count`, а
`order` должен содержать последовательность от `1` до `relay_count`.

### Остальные методы

```http
POST   /admin/relay-results/bulk-create/
GET    /admin/relay-results/?competition_id=<id>
GET    /admin/relay-results/{id}/
DELETE /admin/relay-results/{id}/
```

Bulk-create атомарный: ошибка в одной команде откатывает весь пакет.
Endpoint обновления `PUT` пока отсутствует.

Новые ошибки:

| Код | Имя | HTTP |
|---:|---|---:|
| 3025 | `RELAY_RESULT_NOT_FOUND` | 404 |
| 3026 | `RELAY_ATHLETE_COUNT_MISMATCH` | 422 |
| 3027 | `RELAY_LEG_ORDER_INVALID` | 422 |
| 3028 | `RELAY_ATHLETE_DUPLICATE` | 422 |
| 3029 | `RELAY_COUNT_INVALID` | 422 |

---

## Локации и aliases

### Breaking: alias теперь всегда ведёт на массив

```http
GET /admin/locations/aliases/
```

Старый код:

```ts
type OldCatalog = Record<string, LocationCatalogItem>;
```

Новый код:

```ts
type LocationCatalog =
  Record<string, LocationCatalogItem[]>;
```

Даже один однозначный объект возвращается внутри массива:

```json
{
  "КВВС \"Касатка\"": [
    {
      "id": "...",
      "aliases": ["КВВС \"Касатка\""],
      "club": "КВВС \"Касатка\"",
      "city": "Томск",
      "region": "Томская область",
      "required": []
    }
  ]
}
```

Нельзя больше использовать:

```ts
catalog[alias].id;
```

Нужно:

```ts
const candidates = catalog[alias] ?? [];
```

### Контекстные параметры

```http
GET /admin/locations/aliases/?region_id=<uuid>&city_id=<uuid>
```

Если параметры не переданы, возвращается полный справочник.

Если контекст передан, backend проверяет поля из `required`:

- `required: []` — объект остаётся;
- `required: ["region"]` — нужен совпадающий `region_id`;
- `required: ["city"]` — нужен совпадающий `city_id`;
- `required: ["city", "region"]` — должны совпасть оба.

Если после фильтрации вариантов нет, ключ alias отсутствует в ответе.

### Поиск сущностей

Точное разрешение исходного alias:

```http
GET /admin/locations/aliases/resolve?alias=<exact>&region_id=<uuid>
```

`region_id` необязателен и используется для неоднозначных aliases.

```http
GET /admin/locations/regions/?query=<text>
GET /admin/locations/cities/?query=<text>&region_id=<uuid>
GET /admin/locations/clubs/?query=<text>&region_id=<uuid>&city_id=<uuid>
GET /admin/locations/aliases/search?query=<text>&region_id=<uuid>&city_id=<uuid>
```

Поиск возвращает точные и приблизительные подсказки:

```ts
interface LocationSearchItem {
  id: string;
  name: string;
  exact_match: boolean;
  similarity: number;
}
```

### Создание объекта и добавление alias

Создать новый объект:

```http
POST /admin/locations/aliases/
```

Добавить aliases существующему объекту без создания нового объекта:

```http
POST /admin/locations/aliases/{location_id}/aliases/
```

```json
{
  "aliases": ["Новое исходное название команды"]
}
```

### Создание атлета

Обычное и bulk-создание поддерживают:

```json
{
  "location": {
    "location_id": "uuid",
    "alias": "исходное название команды"
  }
}
```

`alias` должен принадлежать выбранному `location_id`.

Прочитать нормализованные связи атлета:

```http
GET /admin/locations/athletes/{athlete_id}/
```

Старые `athlete.club` и `athlete.city` пока остаются как fallback, но новые
экраны не должны использовать их как источник нормализованных ID.

Ошибки локаций:

| Код | Имя |
|---:|---|
| 3019 | `LOCATION_REGION_REQUIRED` |
| 3020 | `LOCATION_ALIAS_NOT_FOUND` |
| 3021 | `LOCATION_ALIAS_CONFLICT` |
| 3022 | `LOCATION_ALIAS_MISMATCH` |
| 3023 | `LOCATION_ENTITY_ID_CONFLICT` |
| 3024 | `LOCATION_OBJECT_NOT_FOUND` |

---

## Удалённый review-flow

Полностью удалены:

- `ReviewDecision`;
- `ReviewItem`;
- `ReviewSession`;
- review enums и schemas;
- `resolve-candidates`;
- `resolve-preview`;
- `review-sessions`.

Frontend должен удалить:

- импорты сгенерированных review-типов;
- review-страницы и модальные окна;
- вызовы старых review endpoints;
- ветвление по review decision/status.

Вместо review-flow используются поиск локации, точное сопоставление alias,
создание `LocationObject` и добавление alias существующему объекту.

---

## Таблица совместимости

| Изменение | Тип |
|---|---|
| `GET /admin/locations/aliases/`: object → array | **Breaking** |
| удаление review endpoints/types | **Breaking** |
| обязательная обработка `event_type` для relay UI | **Breaking для корректного отображения** |
| relay в `performances` | Additive, но старый UI может показать неверное время |
| relay первого этапа в `top` | Additive |
| `relay_count`, `total_distance` в `Distance` | Additive |
| новые relay admin endpoints | Additive |
| `location` при создании атлета | Additive |
| старые `athlete.club/city` | Пока сохранены |

## Рекомендуемый порядок обновления frontend

1. Перегенерировать Hasura/OpenAPI SDK.
2. Добавить общий `EventType`.
3. Обновить `performances`: для relay показывать `split_result` как личное
   время, `result` как командное.
4. Обновить `top`: учитывать `result.event_type`; relay-время уже находится
   в `result.result`.
5. Обновить подписи дистанций через `relay_count`.
6. Заменить тип aliases на `Record<string, LocationCatalogItem[]>`.
7. Подключить контекст `region_id/city_id`.
8. Удалить review-flow.
9. Подключить нормализованную `location` при создании атлета.
