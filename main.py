import asyncio
import os
from pathlib import Path
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BotCommand, FSInputFile

from config import BOT_TOKEN
from database import (
    init_db, get_player, create_player, add_reward, next_floor,
    get_inventory, get_equipment, equip_item, unequip_item,
    get_battle_session, save_battle_session, delete_battle_session
)
from keyboards import (
    heroes_keyboard, main_keyboard, battle_keyboard, equipment_keyboard
)
from heroes import HEROES
from inventory import inventory_text, equipment_text
from battle import start_battle, battle_turn
from error_handler import setup_error_handler

active_battles = {}

ASSET_DIR = Path(__file__).resolve().parent / "assets"
UI_MOCKUP = ASSET_DIR / "neo_tower_ui.jpg"


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"NeoTowerGameBot is alive")

    def log_message(self, format, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


Thread(target=start_health_server, daemon=True).start()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
setup_error_handler(dp)


async def visual_answer(message: Message, text: str, reply_markup=None):
    if UI_MOCKUP.exists():
        await message.answer_photo(
            FSInputFile(UI_MOCKUP),
            caption=text,
            reply_markup=reply_markup
        )
    else:
        await message.answer(text, reply_markup=reply_markup)


@dp.message(Command("start"))
async def start(message: Message):
    player = get_player(message.from_user.id)

    if player:
        await visual_answer(
            message,
            "🏙️ NEO TOWER\n\nС возвращением! Башня ждёт.",
            main_keyboard()
        )
    else:
        await visual_answer(
            message,
            "🏙️ NEO TOWER\n\nВыбери героя:",
            heroes_keyboard()
        )


@dp.callback_query(lambda c: c.data and c.data.startswith("hero_"))
async def choose_hero(callback: CallbackQuery):
    key = callback.data.replace("hero_", "", 1)
    h = HEROES.get(key)

    if not h:
        await callback.answer("Герой не найден", show_alert=True)
        return

    created = create_player(
        callback.from_user.id,
        callback.from_user.first_name,
        key,
        h["hp"],
        h["damage"],
        h["armor"]
    )

    if not created:
        await callback.message.answer(
            "🧙 Герой уже выбран. Можно сразу идти в бой.",
            reply_markup=main_keyboard()
        )
    else:
        await callback.message.answer(
            f"🧙 {h['name']} выбран!\n\n"
            "⚔️ Железный меч уже экипирован.",
            reply_markup=main_keyboard()
        )

    await callback.answer()


async def run_fight(uid, message):
    p = get_player(uid)

    if not p:
        await visual_answer(
            message,
            "Сначала выбери героя через /start",
            heroes_keyboard()
        )
        return

    state = active_battles.get(uid)
    if state is None:
        state = get_battle_session(uid)

    if state is None:
        state = start_battle(p, p["floor"])
        save_battle_session(uid, state)

    active_battles[uid] = state

    await visual_answer(
        message,
        f"⚔️ БОЙ — этаж {p['floor']}\n\n"
        f"👤 {p['name']}\n"
        f"❤️ Герой: {state['player_hp']} HP\n"
        f"🤖 {state['enemy']['name']}: {state['enemy_hp']} HP\n\n"
        "Выбери действие внизу:",
        battle_keyboard()
    )


async def process_battle_action(uid, message, action):
    p = get_player(uid)

    if not p:
        await visual_answer(
            message,
            "Сначала выбери героя через /start",
            heroes_keyboard()
        )
        return

    state = active_battles.get(uid)
    if state is None:
        state = get_battle_session(uid)

    if state is None:
        state = start_battle(p, p["floor"])

    active_battles[uid] = state

    if action == "escape":
        active_battles.pop(uid, None)
        delete_battle_session(uid)
        await visual_answer(message, "🏃 Побег из боя.", main_keyboard())
        return

    state = battle_turn(p, state, action)
    active_battles[uid] = state

    if state["enemy_hp"] <= 0:
        reward = state["enemy"].get("reward", 100)
        add_reward(uid, 100, reward, "iron_sword")
        next_floor(uid)
        active_battles.pop(uid, None)
        delete_battle_session(uid)

        await visual_answer(
            message,
            f"🏆 ПОБЕДА!\n\n"
            f"💰 Награда: +{reward} кредитов\n"
            "⭐ XP: +100\n"
            "⬆️ Следующий этаж открыт.",
            main_keyboard()
        )

    elif state["player_hp"] <= 0:
        active_battles.pop(uid, None)
        delete_battle_session(uid)

        await visual_answer(
            message,
            "💀 ПОРАЖЕНИЕ\n\n"
            "Герой восстановится перед следующим боем.",
            main_keyboard()
        )

    else:
        save_battle_session(uid, state)
        await visual_answer(
            message,
            f"⚔️ БОЙ ПРОДОЛЖАЕТСЯ\n\n"
            f"❤️ Герой: {state['player_hp']} HP\n"
            f"🤖 Враг: {state['enemy_hp']} HP\n\n"
            "Выбери действие внизу:",
            battle_keyboard()
        )


@dp.callback_query(lambda c: c.data and c.data.startswith("battle_"))
async def battle_action_callback(callback: CallbackQuery):
    action = callback.data.replace("battle_", "", 1)
    await process_battle_action(callback.from_user.id, callback.message, action)
    await callback.answer()


async def process_equipment_action(uid, message, text):
    items = get_inventory(uid)
    item_map = {
        "⚙️ ⚔️ Железный меч": "iron_sword",
        "⚙️ 🛡 Стальная броня": "steel_armor"
    }

    if text in item_map:
        item = item_map[text]
        if equip_item(uid, item):
            equipped = get_equipment(uid)
            await visual_answer(
                message,
                equipment_text(items, equipped),
                equipment_keyboard(items)
            )
        else:
            await message.answer(
                "❌ Этого предмета пока нет в рюкзаке.",
                reply_markup=equipment_keyboard(items)
            )
        return

    if text == "❌ Снять экипировку":
        unequip_item(uid)
        await visual_answer(
            message,
            equipment_text(items, ""),
            equipment_keyboard(items)
        )
        return

    if text == "🔙 В главное меню":
        await visual_answer(message, "🏙️ Главное меню", main_keyboard())


@dp.callback_query(lambda c: c.data and c.data.startswith("equip_"))
async def equip_action(callback: CallbackQuery):
    uid = callback.from_user.id
    item = callback.data.replace("equip_", "", 1)

    if equip_item(uid, item):
        items = get_inventory(uid)
        equipped = get_equipment(uid)
        await visual_answer(
            callback.message,
            equipment_text(items, equipped),
            equipment_keyboard(items)
        )
        await callback.answer("Экипировано")
    else:
        await callback.answer("Предмет недоступен", show_alert=True)


@dp.callback_query(lambda c: c.data == "unequip")
async def unequip_action(callback: CallbackQuery):
    uid = callback.from_user.id
    unequip_item(uid)
    items = get_inventory(uid)

    await visual_answer(
        callback.message,
        equipment_text(items, ""),
        equipment_keyboard(items)
    )
    await callback.answer("Экипировка снята")


@dp.message()
async def menu(message: Message):
    p = get_player(message.from_user.id)

    if message.text == "⚔️ БОЙ":
        await run_fight(message.from_user.id, message)

    elif message.text == "⚔️ АТАКА":
        await process_battle_action(message.from_user.id, message, "attack")

    elif message.text == "🛡 ЗАЩИТА":
        await process_battle_action(message.from_user.id, message, "defend")

    elif message.text == "💊 ЗЕЛЬЕ":
        await process_battle_action(message.from_user.id, message, "potion")

    elif message.text == "🏃 ПОБЕГ":
        await process_battle_action(message.from_user.id, message, "escape")

    elif message.text.startswith("⚙️ "):
        await process_equipment_action(message.from_user.id, message, message.text)

    elif message.text == "❌ Снять экипировку":
        await process_equipment_action(message.from_user.id, message, message.text)

    elif message.text == "🔙 В главное меню":
        await process_equipment_action(message.from_user.id, message, message.text)

    elif message.text == "🎒 РЮКЗАК":
        items = get_inventory(message.from_user.id)
        await visual_answer(
            message,
            inventory_text(items),
            main_keyboard()
        )

    elif message.text == "🧙 ГЕРОЙ":
        if p:
            await visual_answer(
                message,
                f"🧙 ГЕРОЙ\n\n"
                f"❤️ HP: {p['hp']}\n"
                f"⚔️ Урон: {p['damage']}\n"
                f"🛡 Броня: {p['armor']}\n"
                f"🏰 Этаж: {p['floor']}\n"
                f"⭐ XP: {p['xp']}\n"
                f"💰 Кредиты: {p['credits']}",
                main_keyboard()
            )
        else:
            await visual_answer(
                message,
                "Сначала выбери героя через /start",
                heroes_keyboard()
            )

    elif message.text == "🛡 СНАРЯЖЕНИЕ":
        if p:
            items = get_inventory(message.from_user.id)
            equipped = get_equipment(message.from_user.id)
            await visual_answer(
                message,
                equipment_text(items, equipped),
                equipment_keyboard(items)
            )
        else:
            await visual_answer(
                message,
                "Сначала выбери героя через /start",
                heroes_keyboard()
            )

    elif message.text == "🏰 БАШНЯ":
        await visual_answer(
            message,
            f"🏰 БАШНЯ\n\n"
            f"Текущий этаж: {p['floor'] if p else 1}\n"
            "Победи врага, чтобы подняться выше.",
            main_keyboard()
        )

    elif message.text == "🛒 МАГАЗИН":
        await visual_answer(
            message,
            "🛒 МАГАЗИН\n\n"
            "⚔️ Железный меч — уже доступен\n"
            "🛡 Стальная броня — скоро\n\n"
            "Магазин будет расширяться.",
            main_keyboard()
        )

    elif message.text == "🏆 РЕЙТИНГ":
        await visual_answer(
            message,
            "🏆 РЕЙТИНГ\n\n"
            "Таблица лидеров будет добавлена следующим обновлением.",
            main_keyboard()
        )


async def main():
    init_db()
    await bot.set_my_commands([
        BotCommand(command="start", description="🎮 Запуск")
    ])
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
