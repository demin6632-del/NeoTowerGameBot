import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from config import BOT_TOKEN
from database import init_db


bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):

    await message.answer(
        """
🏙️ NEO TOWER


Система запущена.


Добро пожаловать в башню!
        """
    )


async def main():

    init_db()

    print(
        "🏙️ NeoTowerGameBot started"
    )

    await dp.start_polling(
        bot
    )


if __name__ == "__main__":

    asyncio.run(main())
