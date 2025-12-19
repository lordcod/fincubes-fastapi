import asyncio
import typer
from functools import wraps

from app.core.config import settings
from app.models import Athlete, Distance, User
from app.core.security.hashing import hash_password
from tortoise.functions import Count
from tortoise import Tortoise

from app.models.competition.result import CompetitionResult

app = typer.Typer()


def with_db_connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        async def inner():
            await Tortoise.init(db_url=settings.DATABASE_URL,
                                modules={"models": ["app.models"]})
            await Tortoise.generate_schemas()
            try:
                await func(*args, **kwargs)
            finally:
                await Tortoise.close_connections()
        asyncio.run(inner())
    return wrapper


@app.command()
@with_db_connection
async def clear_results(competition_id: int):
    """Удалить результаты по ID соревнования"""
    deleted = await CompetitionResult.filter(competition_id=competition_id).delete()
    print(f"Удалено результатов: {deleted}")


@app.command()
@with_db_connection
async def clear_distances(competition_id: int):
    """Удалить дистанции по ID соревнования"""
    deleted = await Distance.filter(competition_id=competition_id).delete()
    print(f"Удалено дистанций: {deleted}")


@app.command()
@with_db_connection
async def clear_athletes():
    """Удалить спортсменов без результатов"""
    athletes_without_results = await Athlete.annotate(results_count=Count('results')).filter(results_count=0)
    count = len(athletes_without_results)
    for athl in athletes_without_results:
        await athl.delete()
    print(f"Удалено спортсменов без результатов: {count}")


@app.command()
@with_db_connection
async def exchange_cuts(from_athlete_id: int, to_athlete_id: int):
    """Перенести результаты от спортсмена A к спортсмену B и удалить A"""
    athlete_from = await Athlete.get(id=from_athlete_id)
    athlete_to = await Athlete.get(id=to_athlete_id)
    results = await Result.filter(athlete=athlete_from)
    for res in results:
        res.athlete = athlete_to
        await res.save(update_fields=['athlete_id'])
    await athlete_from.delete()
    print(
        f"Результаты перенесены с {from_athlete_id} на {to_athlete_id}, спортсмен {from_athlete_id} удалён.")


@app.command()
@with_db_connection
async def check_athletes():
    """Проверить спортсменов на дубликаты и некорректные данные"""
    athletes = await Athlete.all()
    uniq = {}
    for athl in athletes:
        data = (athl.first_name, athl.last_name, athl.birth_year)
        if len(athl.birth_year) == 2:
            print('Удалить из-за короткого года рождения:', *data, athl.id)
            await athl.delete()
            continue
        if data in uniq:
            print('Дубликат:', *data, athl.id, 'и', uniq[data].id)
        else:
            uniq[data] = athl
    print("Проверка завершена.")


@app.command()
@with_db_connection
async def change_password():
    """Изменить пароль пользователя с интерактивным вводом"""
    import getpass
    user_id = int(typer.prompt("Введите ID пользователя"))
    password = getpass.getpass("Введите новый пароль: ")
    user = await User.filter(id=user_id).first()
    if not user:
        print("Пользователь не найден")
        return
    user.hashed_password = hash_password(password)
    await user.save()
    print(f"Пароль пользователя {user_id} успешно изменён.")


if __name__ == "__main__":
    app()
