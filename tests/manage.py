import asyncio
import typer
from functools import wraps
from typing import Optional

from app.core.config import settings
from app.models import Athlete, Result, Distance, User
from app.core.security.hashing import hash_password
from app.services import admin_maintenance
from tortoise.functions import Count
from tortoise import Tortoise

app = typer.Typer()


def print_maintenance_result(result):
    data = result.model_dump()
    for key, value in data.items():
        if key == "messages":
            continue
        print(f"{key}: {value}")
    for message in result.messages:
        print(message)


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
    result = await admin_maintenance.clear_results(competition_id=competition_id, apply=True)
    print_maintenance_result(result)


@app.command()
@with_db_connection
async def clear_distances(competition_id: int):
    """Удалить дистанции по ID соревнования"""
    result = await admin_maintenance.clear_distances(competition_id=competition_id, apply=True)
    print_maintenance_result(result)


@app.command()
@with_db_connection
async def clear_athletes():
    """Удалить спортсменов без результатов"""
    result = await admin_maintenance.clear_empty_athletes(apply=True)
    print_maintenance_result(result)


@app.command()
@with_db_connection
async def exchange_cuts(from_athlete_id: int, to_athlete_id: int):
    """Перенести результаты от спортсмена A к спортсмену B и удалить A"""
    result = await admin_maintenance.transfer_results(
        from_athlete_id=from_athlete_id,
        to_athlete_id=to_athlete_id,
        apply=True,
        delete_empty_source=True,
    )
    print_maintenance_result(result)


@app.command()
@with_db_connection
async def transfer_results(
    from_athlete_id: int,
    to_athlete_id: int,
    competition_id: Optional[int] = None,
    apply: bool = False,
    delete_empty_source: bool = False,
):
    """Safely move results from one athlete to another.

    By default this is a dry-run. Pass --apply to actually update rows.
    Use --competition-id to move only one competition instead of all results.
    """
    result = await admin_maintenance.transfer_results(
        from_athlete_id=from_athlete_id,
        to_athlete_id=to_athlete_id,
        competition_id=competition_id,
        apply=apply,
        delete_empty_source=delete_empty_source,
    )
    print_maintenance_result(result)


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
