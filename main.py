import asyncio
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BotCommand
from config import BOT_TOKEN
from database import init_db, get_player, create_player, add_reward, next_floor
from keyboards import heroes_keyboard, main_keyboard, battle_keyboard
from heroes import HEROES
from inventory import inventory_text, starter_inventory
from battle import fight
from error_handler import setup_error_handler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"NeoTowerGameBot is alive")
    def log_message(self, format, *args): pass

Thread(target=lambda: HTTPServer(("0.0.0.0", int(os.environ.get("PORT",10000))), HealthHandler).serve_forever(), daemon=True).start()

bot=Bot(token=BOT_TOKEN)
dp=Dispatcher()
setup_error_handler(dp)

@dp.message(Command("start"))
async def start(message: Message):
    player=get_player(message.from_user.id)
    await message.answer("🏙️ NEO TOWER", reply_markup=main_keyboard() if player else heroes_keyboard())

@dp.callback_query(lambda c:c.data.startswith("hero_"))
async def choose_hero(callback:CallbackQuery):
    h=HEROES[callback.data.replace("hero_","")]
    create_player(callback.from_user.id,callback.from_user.first_name,callback.data.replace("hero_",""),h["hp"],h["damage"],h["armor"])
    await callback.message.answer(f"🧙 {h['name']} выбран!",reply_markup=main_keyboard())
    await callback.answer()

async def run_fight(uid,message):
    p=get_player(uid)
    if not p:
        await message.answer("Выбери героя через /start"); return
    await message.answer(f"⚔️ Бой начался!\n\n🤖 Враг на этаже {p['floor']}\n\nВыбери действие:",reply_markup=battle_keyboard())

@dp.callback_query(lambda c:c.data.startswith("battle_"))
async def battle_action(callback:CallbackQuery):
    p=get_player(callback.from_user.id)
    if not p: return
    if callback.data=="battle_escape":
        await callback.message.answer("🏃 Ты сбежал",reply_markup=main_keyboard())
    else:
        result=fight(p,p['floor'])
        text="⚔️ Результат боя:\n\n"+"\n".join(result['log'])
        if result['win']:
            add_reward(callback.from_user.id,100,result['reward'],"iron_sword")
            next_floor(callback.from_user.id)
            text+="\n\n🏆 Победа!"
        else: text+="\n\n💀 Поражение"
        await callback.message.answer(text,reply_markup=main_keyboard())
    await callback.answer()

@dp.message()
async def menu(message:Message):
    if message.text=="⚔️ БОЙ": await run_fight(message.from_user.id,message)
    elif message.text=="🎒 РЮКЗАК": await message.answer(inventory_text(starter_inventory()),reply_markup=main_keyboard())
    elif message.text=="🏰 БАШНЯ": await message.answer("🏰 Башня",reply_markup=main_keyboard())
    elif message.text=="🧙 ГЕРОЙ": await message.answer("🧙 Герой",reply_markup=main_keyboard())
    elif message.text=="🛡 СНАРЯЖЕНИЕ": await message.answer("🛡 Снаряжение",reply_markup=main_keyboard())
    elif message.text=="🛒 МАГАЗИН": await message.answer("🛒 Магазин",reply_markup=main_keyboard())
    elif message.text=="🏆 РЕЙТИНГ": await message.answer("🏆 Рейтинг",reply_markup=main_keyboard())

@dp.message(Command("fight"))
async def fight_cmd(message:Message): await run_fight(message.from_user.id,message)

async def main():
    init_db()
    await bot.set_my_commands([BotCommand(command="start",description="🎮 Запуск"),BotCommand(command="fight",description="⚔️ Бой")])
    await dp.start_polling(bot)

if __name__=="__main__": asyncio.run(main())
