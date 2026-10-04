import logging
import traceback
import uuid

from aiogram import Router
from aiogram.types import ErrorEvent

router = Router()
logger = logging.getLogger("neotower")


@router.error()
async def error_handler(event: ErrorEvent):
    error_id = uuid.uuid4().hex[:8]
    logger.error(
        "BOT ERROR id=%s type=%s message=%s\n%s",
        error_id,
        type(event.exception).__name__,
        event.exception,
        "".join(traceback.format_exception(event.exception)),
    )
    return True


def setup_error_handler(dp):
    dp.include_router(router)
