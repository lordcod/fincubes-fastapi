import asyncio
from tortoise import Tortoise

from app.core.config import settings
from app.core.security.schema import TokenType
from app.core.security.token import _create_token as create_jwt_token
from app.models.misc.bot import Bot


async def main():
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()
    bot = await Bot.create(
        name="nextjs_full_access_bot",
        owner_id=2,
        scopes=["*"],
        is_active=True
    )
    token = create_jwt_token(
        subject=bot.id,
        type_token=TokenType.service,
        issuer=f"user:{bot.owner_id}",
        audience="nextjs",
        scopes=["*"]
    )
    print(token)
    await Tortoise.close_connections()


if __name__ == '__main__':
    asyncio.run(main())
