from tortoise.transactions import in_transaction

from app.shared.utils.templates import get_sql


async def fix_resolved_time_column():
    async with in_transaction() as conn:
        search_sql = await get_sql('search_resolved_time.sql')
        result = await conn.execute_query_dict(search_sql)
        if result:
            is_generated = result[0].get('is_generated')
            if is_generated != 'ALWAYS':
                drop_sql = await get_sql('drop_resolved_time.sql')
                add_sql = await get_sql('add_resolved_time.sql')
                await conn.execute_script(drop_sql)
                await conn.execute_script(add_sql)
        else:
            add_sql = await get_sql('add_resolved_time.sql')
            await conn.execute_script(add_sql)
