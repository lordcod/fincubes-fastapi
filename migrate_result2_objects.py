import asyncio
import logging
from tortoise import Tortoise
from tortoise.transactions import in_transaction
from tortoise.expressions import Q

from app.core.config import settings
from app.models import Result, CompetitionResult, CompetitionStage
BATCH_SIZE = 1000

logger = logging.getLogger(__name__)


async def migrate_result2_objects_bulk(queryset=None):
    if queryset is None:
        queryset = Result.filter(Q(metadata={}) | Q(metadata__isnull=True))

    finals_set = set(
        await Result.filter(
            final__not_isnull=True,
            metadata={}
        ).values_list("competition_id", "stroke", "distance")
    )

    total = await queryset.count()
    logger.info("Starting migration, total candidates: %d", total)

    processed = 0
    batch = 0
    last_id = 0

    while True:
        results = await queryset \
            .filter(id__gt=last_id) \
            .order_by("id") \
            .limit(BATCH_SIZE)

        if not results:
            break

        batch += 1
        cr_objects = []
        cs_objects = []

        for rec in results:
            has_final = (rec.competition_id, rec.stroke,
                         rec.distance) in finals_set

            cr_objects.append(
                CompetitionResult(
                    id=rec.id,
                    stroke=rec.stroke,
                    distance=rec.distance,
                    points=rec.points,
                    record=rec.record,
                    athlete_id=rec.athlete_id,
                    competition_id=rec.competition_id,
                    resolved_time=rec.resolved_time,
                )
            )

            if rec.final is None:
                cs_objects.append(
                    CompetitionStage(
                        result_id=rec.id,
                        kind='HEAT' if has_final else 'RESULT',
                        order=1,
                        time=rec.result if rec.status.upper() in ('COMPLETED', 'EXH') else None,
                        status=rec.status.upper(),
                        place=rec.place,
                        rank=rec.final_rank,
                    )
                )
            else:
                cs_objects.append(
                    CompetitionStage(
                        result_id=rec.id,
                        kind='HEAT',
                        order=1,
                        time=rec.result if rec.status.upper() in ('COMPLETED', 'EXH') else None,
                        status=rec.status.upper(),
                        rank=rec.final_rank,
                    )
                )

                stage2_status = 'DSQ' if rec.status.upper() == 'DSQ_FINAL' else rec.status.upper()

                cs_objects.append(
                    CompetitionStage(
                        result_id=rec.id,
                        kind='FINAL',
                        order=2,
                        time=rec.result if stage2_status in (
                            'COMPLETED', 'EXH') else None,
                        status=stage2_status,
                        place=rec.place,
                    )
                )

        await CompetitionResult.bulk_create(cr_objects, ignore_conflicts=True)
        await CompetitionStage.bulk_create(cs_objects)

        processed += len(results)
        last_id = results[-1].id

        logger.info(
            "Batch %d | processed: %d/%d | cr: %d | cs: %d",
            batch,
            processed,
            total,
            len(cr_objects),
            len(cs_objects)
        )

    logger.info("Migration finished. Total processed: %d", processed)


async def migrate_missing_results():
    missing_ids = await Result.raw("""
        SELECT r.id
        FROM results2 r
        LEFT JOIN competition_results cr ON cr.id = r.id
        WHERE (r.metadata = '{}' or r.metadata IS NULL) AND cr.id IS NULL;
    """)

    ids = [r.id for r in missing_ids]

    if not ids:
        print("Нет пропущенных результатов")
        return

    print(f"Найдено {len(ids)} пропущенных результатов")

    await migrate_result2_objects_bulk(
        queryset=Result.filter(id__in=ids)
    )


async def migrate_results_with_metadata():
    queryset = Result.exclude(metadata={})  # берем только строки с metadata

    async for rec in queryset:
        result_obj = await CompetitionResult.create(
            id=rec.id,
            stroke=rec.stroke,
            distance=rec.distance,
            points=rec.points,
            record=rec.record,
            athlete_id=rec.athlete_id,
            competition_id=rec.competition_id,
            resolved_time=rec.resolved_time
        )

        attempts = rec.metadata['attempts']
        total = len(attempts)

        for idx, attempt in enumerate(attempts):
            kind = "HEAT" if idx == 0 else "FINAL" if idx == total - 1 else f"SEMIFINAL"
            code = None
            if kind == "SEMIFINAL":
                code = chr(65 + idx - 1)
            await CompetitionStage.create(
                result=result_obj,
                kind=kind,
                order=idx + 1,
                code=code,
                time=attempt,
                status=rec.status.upper(),
                place=rec.place if idx == total - 1 else None,
                rank=rec.final_rank if idx == total - 1 else None,
            )


async def main():
    logging.basicConfig(level=logging.INFO)
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()
    await migrate_results_with_metadata()
    await Tortoise.close_connections()


if __name__ == '__main__':
    asyncio.run(main())
