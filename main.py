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
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

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
    await callback.message.answer(f"🧙 {hero['name']} выбран!", reply_markup=main_keyboard())
    await callback.answer()


async def run_fight(user_id, message):
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала выбери героя через /start")
        return
    result = fight(player, player["floor"])
    text = "⚔️ Бой завершён\n\n" + "\n".join(result["log"])
    if result["win"]:
        add_reward(user_id, 100, result["reward"], "iron_sword")
        next_floor(user_id)
        text += "\n\n🏆 Победа!"
    else:
        text += "\n\n💀 Поражение"
    await message.answer(text, reply_markup=main_keyboard())


@dp.message()
async def menu_buttons(message: Message):
    buttons = {
        "⚔️ БОЙ": "fight",
        "🏰 БАШНЯ": "tower",
        "🧙 ГЕРОЙ": "hero",
        "🎒 РЮКЗАК": "inventory",
        "🛡 СНАРЯЖЕНИЕ": "equipment",
        "🛒 МАГАЗИН": "shop",
        "🏆 РЕЙТИНГ": "rating",
    }
    if message.text == "⚔️ БОЙ":
        await run_fight(message.from_user.id, message)
    elif message.text in buttons:
        await message.answer(f"Открыт раздел: {buttons[message.text]}", reply_markup=main_keyboard())


@dp.message(Command("fight"))
async def fight_command(message: Message):
    await run_fight(message.from_user.id, message)


async def main():
    init_db()
    await bot.set_my_commands([
        BotCommand(command="start", description="🎮 Запустить игру"),
        BotCommand(command="fight", description="⚔️ Бой"),
    ])
    print("NeoTowerGameBot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
