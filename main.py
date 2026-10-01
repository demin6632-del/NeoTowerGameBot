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
from inventory import inventory_text, equipment_text, starter_inventory
from battle import start_battle, battle_turn
from error_handler import setup_error_handler

active_battles = {}

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"NeoTowerGameBot is alive")
    def log_message(self, format, *args):
        pass

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
    key=callback.data.replace("hero_","")
    h=HEROES[key]
    create_player(callback.from_user.id,callback.from_user.first_name,key,h["hp"],h["damage"],h["armor"])
    await callback.message.answer(f"🧙 {h['name']} выбран!",reply_markup=main_keyboard())
    await callback.answer()

async def run_fight(uid,message):
    p=get_player(uid)
    if not p:
        await message.answer("Сначала выбери героя через /start")
        return
    if uid not in active_battles:
        active_battles[uid]=start_battle(p,p['floor'])
    state=active_battles[uid]
    await message.answer(f"⚔️ Бой\n\n❤️ Герой: {state['player_hp']}\n🤖 Враг: {state['enemy_hp']}",reply_markup=battle_keyboard())

@dp.callback_query(lambda c:c.data.startswith("battle_"))
async def battle_action(callback:CallbackQuery):
    uid=callback.from_user.id
    p=get_player(uid)
    if not p:
        await callback.answer()
        return
    if uid not in active_battles:
        active_battles[uid]=start_battle(p,p['floor'])
    action=callback.data.replace("battle_","")
    if action=="escape":
        active_battles.pop(uid,None)
        await callback.message.answer("🏃 Побег",reply_markup=main_keyboard())
    else:
        state=battle_turn(p,active_battles[uid],action)
        if state['enemy_hp']<=0:
            add_reward(uid,100,state['enemy'].get('credits',100),"iron_sword")
            next_floor(uid)
            active_battles.pop(uid,None)
            await callback.message.answer("🏆 Победа!",reply_markup=main_keyboard())
        elif state['player_hp']<=0:
            active_battles.pop(uid,None)
            await callback.message.answer("💀 Поражение",reply_markup=main_keyboard())
        else:
            await callback.message.answer(f"⚔️ Бой продолжается\n❤️ {state['player_hp']} HP\n🤖 {state['enemy_hp']} HP",reply_markup=battle_keyboard())
    await callback.answer()

@dp.message()
async def menu(message:Message):
    p=get_player(message.from_user.id)
    items=starter_inventory()
    if message.text=="⚔️ БОЙ":
        await run_fight(message.from_user.id,message)
    elif message.text=="🎒 РЮКЗАК":
        await message.answer(inventory_text(items),reply_markup=main_keyboard())
    elif message.text=="🧙 ГЕРОЙ":
        if p:
            await message.answer(f"🧙 Герой\n❤️ HP: {p['hp']}\n⚔️ Урон: {p['damage']}\n🛡 Броня: {p.get('armor',0)}",reply_markup=main_keyboard())
    elif message.text=="🛡 СНАРЯЖЕНИЕ":
        await message.answer(equipment_text(items),reply_markup=main_keyboard())
    elif message.text=="🏰 БАШНЯ":
        await message.answer(f"🏰 Башня\nЭтаж: {p['floor'] if p else 1}",reply_markup=main_keyboard())

async def main():
    init_db()
    await bot.set_my_commands([BotCommand(command="start",description="🎮 Запуск")])
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
