import asyncio
from app.shared.clients.redis import client


async def delete_keys_by_pattern(pattern):
    """
    Удаляет все ключи, которые соответствуют шаблону (асинхронно).
    :param pattern: шаблон ключей, например 'user:*'
    """
    keys_to_delete = []

    async for key in client.scan_iter(match=pattern):
        keys_to_delete.append(key)

    if not keys_to_delete:
        print("Ключи не найдены")
        return

    await client.delete(*keys_to_delete)
    print(f"Удалено {len(keys_to_delete)} ключей")

asyncio.run(delete_keys_by_pattern("performances:*"))
