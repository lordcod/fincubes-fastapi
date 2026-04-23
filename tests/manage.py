import asyncio
import typer
from functools import wraps
from typing import Optional

from app.core.config import settings
from app.models import Athlete, Result, Distance, User
from app.core.security.hashing import hash_password
from tortoise.functions import Count
from tortoise import Tortoise

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
    deleted = await Result.filter(competition_id=competition_id).delete()
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
async def transfer_results(
    from_athlete_id: int,
    to_athlete_id: int,
    competition_id: int,
    apply: bool = False
):
    """Safely move results from one athlete to another.

    By default this is a dry-run. Pass --apply to actually update rows.
    Use --competition-id to move only one competition instead of all results.
    """
    if from_athlete_id == to_athlete_id:
        print("from_athlete_id and to_athlete_id must be different")
        return

    athlete_from = await Athlete.get_or_none(id=from_athlete_id)
    if not athlete_from:
        print(f"Source athlete not found: {from_athlete_id}")
        return

    athlete_to = await Athlete.get_or_none(id=to_athlete_id)
    if not athlete_to:
        print(f"Target athlete not found: {to_athlete_id}")
        return

    query = Result.filter(athlete_id=from_athlete_id)
    if competition_id is not None:
        query = query.filter(competition_id=competition_id)

    results = await query.order_by("competition_id", "id").all()
    if not results:
        print("No results to transfer.")
        return

    print("Transfer preview")
    print(
        f"FROM #{athlete_from.id}: {athlete_from.last_name} {athlete_from.first_name} "
        f"{athlete_from.birth_year} {athlete_from.gender}"
    )
    print(
        f"TO   #{athlete_to.id}: {athlete_to.last_name} {athlete_to.first_name} "
        f"{athlete_to.birth_year} {athlete_to.gender}"
    )
    print(
        f"competition_id: {competition_id if competition_id is not None else 'ALL'}")
    print(f"results: {len(results)}")

    competitions: dict[int, int] = {}
    for result in results:
        competitions[result.competition_id] = competitions.get(
            result.competition_id, 0) + 1
    for comp_id, count in sorted(competitions.items()):
        print(f"  competition #{comp_id}: {count} result(s)")

    if not apply:
        print("Dry-run only. Re-run with --apply to move these results.")
        return

    for result in results:
        result.athlete_id = to_athlete_id

    await Result.bulk_update(results, ["athlete_id"])
    print(
        f"Moved {len(results)} result(s) from athlete #{from_athlete_id} to #{to_athlete_id}.")

    remaining = await Result.filter(athlete_id=from_athlete_id).count()
    print(f"Source athlete remaining results: {remaining}")


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
