# Relay results API

Эстафетные результаты хранятся отдельно от индивидуальных `Result`.
Название команды сохраняется буквально в поле `name`; ссылок на объект
локации или `distance_id` нет.

## Семантика дистанции

- `distance` — длина одного этапа;
- `relay_count` — количество этапов;
- `total_distance` возвращается API и вычисляется как
  `distance * relay_count`;
- для `RelayResult` значение `relay_count` должно быть больше `1`.

Например, `4 x 50` передаётся как:

```json
{
  "distance": 50,
  "relay_count": 4
}
```

В ответе `total_distance` будет равен `200`.

## Создание одного результата

```http
POST /admin/relay-results/
```

Scope: `result:create`.

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

Результат и все этапы создаются одной транзакцией.

Обязательные проверки:

- соревнование существует;
- все атлеты существуют;
- количество `legs` равно `relay_count`;
- `order` содержит последовательность от `1` до `relay_count`;
- один `athlete_id` не повторяется в составе;
- `distance > 0`;
- `relay_count > 1`.

## Массовое создание

```http
POST /admin/relay-results/bulk-create/
```

Scope: `result:create`.

Тело запроса — массив объектов того же формата, что и одиночное создание.
Весь массив обрабатывается одной транзакцией. Ошибка в любой команде
откатывает создание всего пакета.

## Получение результатов

```http
GET /admin/relay-results/?competition_id=123
```

Scope: `result:read`.

Дополнительные точные фильтры:

- `stroke`;
- `distance`;
- `relay_count`;
- `gender`.

Получение одного результата:

```http
GET /admin/relay-results/{id}/
```

Ответ содержит вычисленный `total_distance` и отсортированный по `order`
массив `legs`.

## Удаление

```http
DELETE /admin/relay-results/{id}/
```

Scope: `result:delete`.

Возвращает `204 No Content`. Все `RelayLeg` этого результата удаляются
каскадно.

## Коды ошибок

| Код | Имя | HTTP | Причина |
|---:|---|---:|---|
| 3001 | `ATHLETE_NOT_FOUND` | 404 | хотя бы один атлет не найден |
| 3002 | `COMPETITION_NOT_FOUND` | 404 | соревнование не найдено |
| 3025 | `RELAY_RESULT_NOT_FOUND` | 404 | результат эстафеты не найден |
| 3026 | `RELAY_ATHLETE_COUNT_MISMATCH` | 422 | неверное количество этапов |
| 3027 | `RELAY_LEG_ORDER_INVALID` | 422 | неверная последовательность `order` |
| 3028 | `RELAY_ATHLETE_DUPLICATE` | 422 | атлет повторяется в составе |
| 3029 | `RELAY_COUNT_INVALID` | 422 | `relay_count` меньше или равен `1` |
