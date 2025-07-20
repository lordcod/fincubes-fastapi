from app.shared.enums.enums import GenderEnum


categories = [
    {
        "name": "Малыши",
        "id": "kids",
        "min_age": 0,
        "max_age": 9
    },
    {
        "name": "Юные",
        "id": "young",
        "min_age": 10,
        "max_age": 11
    },
    {
        "name": "Юниоры",
        "id": "junior",
        "min_age": 12,
        "max_age": 13
    },
    {
        "name": "Кадеты",
        "id": "cadet",
        "min_age": 14,
        "max_age": 15
    },
    {
        "name": "Юниоры старшие",
        "id": "junior_senior",
        "min_age": 16,
        "max_age": 17
    },
    {
        "name": "Молодёжь",
        "id": "youth",
        "min_age": 18,
        "max_age": 21
    },
    {
        "name": "Взрослые",
        "id": "adult",
        "min_age": 22,
        "max_age": 34
    },
    {
        "name": "Мастера",
        "id": "masters",
        "min_age": 35,
        "max_age": 44
    },
    {
        "name": "Легенды",
        "id": "legends",
        "min_age": 45,
        "max_age": 150
    },
    {
        "name": "Общий зачёт",
        "id": "absolute",
        "min_age": None,
        "max_age": None
    }
]


swim_styles = [
    {"stroke": "APNEA", "distance": 50},
    {"stroke": "BIFINS", "distance": 50},
    {"stroke": "BIFINS", "distance": 100},
    {"stroke": "BIFINS", "distance": 200},
    {"stroke": "BIFINS", "distance": 400},
    {"stroke": "IMMERSION", "distance": 100},
    {"stroke": "IMMERSION", "distance": 400},
    {"stroke": "SURFACE", "distance": 50},
    {"stroke": "SURFACE", "distance": 100},
    {"stroke": "SURFACE", "distance": 200},
    {"stroke": "SURFACE", "distance": 400},
    {"stroke": "SURFACE", "distance": 800},
    {"stroke": "SURFACE", "distance": 1500},
]

genders = [value.value for value in GenderEnum]

COMBINATIONS = [
    (style, gender, category)
    for style in swim_styles
    for gender in genders
    for category in categories
]
