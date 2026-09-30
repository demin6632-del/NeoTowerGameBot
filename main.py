import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import BOT_TOKEN
from database import init_db, get_player, create_player
from keyboards import heroes_keyboard, main_keyboard
from heroes import HEROES


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):

    player = get_player(message.from_user.id)

    if player:
        await message.answer(
            "🏙️ NEO TOWER\n\nТы уже в игре.",
            reply_markup=main_keyboard()
        )
    else:
        await message.answer(
            "🏙️ NEO TOWER\n\nВыбери своего героя:",
            reply_markup=heroes_keyboard()
        )


@dp.callback_query(lambda c: c.data.startswith("hero_"))
async def choose_hero(callback: CallbackQuery):

    hero_id = callback.data.replace("hero_", "")
    hero = HEROES[hero_id]

    create_player(
        callback.from_user.id,
        callback.from_user.first_name,
        hero_id,
        hero["hp"],
        hero["damage"],
        hero["armor"]
    )

    await callback.message.edit_text(
        f"{hero['name']} выбран!\n\nДобро пожаловать в башню.",
        reply_markup=main_keyboard()
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "profile")
async def profile(callback: CallbackQuery):

    player = get_player(callback.from_user.id)

    await callback.message.answer(
        f"👤 Профиль\n\nУровень: {player['level']}\nXP: {player['xp']}\nЭтаж: {player['floor']}\nКредиты: {player['credits']}"
    )


async def main():

    init_db()

    print("🏙️ NeoTowerGameBot started")

    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())
