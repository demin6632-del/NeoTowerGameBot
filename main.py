import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import BOT_TOKEN
from database import init_db, get_player, create_player
from keyboards import heroes_keyboard, main_keyboard
from heroes import HEROES
from battle import create_enemy, attack, enemy_attack

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    player = get_player(message.from_user.id)
    if player:
        await message.answer("🏙️ NEO TOWER\n\nТы уже в игре.", reply_markup=main_keyboard())
    else:
        await message.answer("🏙️ NEO TOWER\n\nВыбери героя:", reply_markup=heroes_keyboard())


@dp.message(Command("fight"))
async def fight(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала выбери героя через /start")
        return

    enemy = create_enemy(player["floor"])
    damage = attack(player["damage"])
    enemy_hp = enemy["hp"] - damage

    if enemy_hp <= 0:
        await message.answer(f"⚔️ Победа!\n\nТы победил {enemy['enemy']}\n+{enemy['credits']} кредитов")
    else:
        taken = enemy_attack(enemy["damage"], player["armor"])
        await message.answer(f"⚔️ Бой продолжается!\n\nТы нанёс {damage} урона.\nВраг нанёс {taken} урона.")


@dp.callback_query(lambda c: c.data.startswith("hero_"))
async def choose_hero(callback: CallbackQuery):
    hero_id = callback.data.replace("hero_", "")
    hero = HEROES[hero_id]
    create_player(callback.from_user.id, callback.from_user.first_name, hero_id, hero["hp"], hero["damage"], hero["armor"])
    await callback.message.edit_text(f"{hero['name']} выбран!", reply_markup=main_keyboard())
    await callback.answer()


@dp.callback_query(lambda c: c.data == "profile")
async def profile(callback: CallbackQuery):
    player = get_player(callback.from_user.id)
    await callback.message.answer(f"👤 Уровень: {player['level']}\nXP: {player['xp']}\nЭтаж: {player['floor']}\nКредиты: {player['credits']}")


@dp.callback_query(lambda c: c.data == "tower")
async def tower(callback: CallbackQuery):
    await callback.message.answer("🏢 Башня. Первый этаж готов. Используй /fight")


@dp.callback_query(lambda c: c.data == "inventory")
async def inventory(callback: CallbackQuery):
    await callback.message.answer("🎒 Инвентарь подключается")


@dp.callback_query(lambda c: c.data == "equipment")
async def equipment(callback: CallbackQuery):
    await callback.message.answer("🛡 Экипировка подключается")


async def main():
    init_db()
    print("NeoTowerGameBot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
