from aiogram import Router
from aiogram.types import ErrorEvent

router = Router()


@router.error()
async def error_handler(event: ErrorEvent):
    print(f"BOT ERROR: {event.exception}")
    return True
