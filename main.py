import asyncio
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BotCommand

from config import BOT_TOKEN
from database import init_db, get_player, create_player, add_reward, next_floor
from keyboards import heroes_keyboard, main_keyboard
from heroes import HEROES
from inventory import inventory_text, starter_inventory
from battle import fight
from error_handler import setup_error_handler


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"NeoTowerGameBot is alive")

    def log_message(self, format, *args):
        pass


def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

Thread(target=run_health_server, daemon=True).start()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
setup_error_handler(dp)


@dp.message(Command("start"))
async def start(message: Message):
    player = get_player(message.from_user.id)
    if player:
        await message.answer("🏙️ NEO TOWER\n\nДобро пожаловать обратно!", reply_markup=main_keyboard())
    else:
        await message.answer("🏙️ NEO TOWER\n\nВыбери героя:", reply_markup=heroes_keyboard())


@dp.callback_query(lambda c: c.data.startswith("hero_"))
async def choose_hero(callback: CallbackQuery):
    hero_id = callback.data.replace("hero_", "")
    hero = HEROES[hero_id]
    create_player(callback.from_user.id, callback.from_user.first_name, hero_id, hero["hp"], hero["damage"], hero["armor"])
    await callback.message.edit_text(f"🧙 {hero['name']} выбран!", reply_markup=main_keyboard())
    await callback.answer()


@dp.callback_query(lambda c: c.data == "fight")
async def fight_button(callback: CallbackQuery):
    player = get_player(callback.from_user.id)
    if not player:
        await callback.message.answer("Сначала выбери героя через /start")
        return
    result = fight(player, player["floor"])
    text = "⚔️ Бой завершён\n\n" + "\n".join(result["log"])
    if result["win"]:
        add_reward(callback.from_user.id, 100, result["reward"], "iron_sword")
        next_floor(callback.from_user.id)
        text += "\n\n🏆 Победа!"
    else:
        text += "\n\n💀 Поражение"
    await callback.message.answer(text)
    await callback.answer()


@dp.message(Command("fight"))
async def fight_command(message: Message):
    await fight_button(type("Obj", (), {"from_user": message.from_user, "message": message, "answer": lambda: None})())


@dp.callback_query(lambda c: c.data == "inventory")
async def inventory(callback: CallbackQuery):
    await callback.message.answer(inventory_text(starter_inventory()))


@dp.callback_query(lambda c: c.data == "equipment")
async def equipment(callback: CallbackQuery):
    await callback.message.answer("🛡 Экипировка:\n\n⚔️ Железный меч (+10 урон)")


@dp.callback_query(lambda c: c.data == "profile")
async def profile(callback: CallbackQuery):
    player = get_player(callback.from_user.id)
    if not player:
        await callback.message.answer("Сначала выбери героя через /start")
        return
    await callback.message.answer(f"👤 Уровень: {player['level']}\nXP: {player['xp']}\nЭтаж: {player['floor']}\n💰 Кредиты: {player['credits']}")


@dp.callback_query(lambda c: c.data == "hero")
async def hero_page(callback: CallbackQuery):
    await callback.message.answer("🧙 Герой\n\nХарактеристики и улучшения скоро доступны.")


@dp.callback_query(lambda c: c.data == "tower")
async def tower(callback: CallbackQuery):
    player = get_player(callback.from_user.id)
    floor = player['floor'] if player else 1
    await callback.message.answer(f"🏰 Neo Tower\n\nТекущий этаж: {floor}\n\n⚔️ Готовься к бою!")


@dp.callback_query(lambda c: c.data == "shop")
async def shop(callback: CallbackQuery):
    await callback.message.answer("🛒 Магазин\n\n⚔️ Железный меч — 100 монет\n💊 Зелье — 50 монет")


@dp.callback_query(lambda c: c.data == "rating")
async def rating(callback: CallbackQuery):
    await callback.message.answer("🏆 Рейтинг\n\n1. Игроки Neo Tower\n\nСкоро здесь будет таблица лидеров.")


async def main():
    init_db()
    await bot.set_my_commands([
        BotCommand(command="start", description="🎮 Запустить игру"),
        BotCommand(command="profile", description="👤 Профиль"),
        BotCommand(command="tower", description="🏰 Башня"),
        BotCommand(command="fight", description="⚔️ Бой"),
        BotCommand(command="inventory", description="🎒 Инвентарь"),
        BotCommand(command="equipment", description="🛡 Экипировка"),
        BotCommand(command="help", description="❓ Помощь"),
    ])
    print("NeoTowerGameBot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
