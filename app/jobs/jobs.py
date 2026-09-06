import logging
from app.models.user.user import User
from app.repositories.ratings import update_ratings
from app.shared.clients.mongodb import db
from app.services.athlete_license import sync_athlete_licenses

logger = logging.getLogger(__name__)


async def daily_task():
    await update_ratings(db['ranking'])
    await sync_athlete_licenses()
    logger.info("Daily ratings task completed")


async def delete_unverified_user(user_id: int):
    user = await User.get_or_none(id=user_id)
    if user and not user.verified:
        logger.info("Deleting unverified user %s", user.email)
        await user.delete()
    else:
        logger.debug("User %s already verified or not found", user_id)
