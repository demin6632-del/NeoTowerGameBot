import asyncio
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BotCommand
from config import BOT_TOKEN
from database import (
    init_db, get_player, create_player, add_reward, next_floor,
    get_inventory, get_equipment, equip_item, unequip_item
)
from keyboards import (
    heroes_keyboard, main_keyboard, battle_keyboard, equipment_keyboard
)
from heroes import HEROES
from inventory import inventory_text, equipment_text
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


Thread(
    target=lambda: HTTPServer(
        ("0.0.0.0", int(os.environ.get("PORT", 10000))),
        HealthHandler
    ).serve_forever(),
    daemon=True
).start()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
setup_error_handler(dp)


@dp.message(Command("start"))
async def start(message: Message):
    player = get_player(message.from_user.id)

    if player:
        await message.answer(
            "🏙️ NEO TOWER\n\nС возвращением! Башня ждёт.",
            reply_markup=main_keyboard()
        )
    else:
        await message.answer(
            "🏙️ NEO TOWER\n\nВыбери героя:",
            reply_markup=heroes_keyboard()
        )


@dp.callback_query(lambda c: c.data.startswith("hero_"))
async def choose_hero(callback: CallbackQuery):
    key = callback.data.replace("hero_", "")
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
        await message.answer(
            "Сначала выбери героя через /start",
            reply_markup=heroes_keyboard()
        )
        return

    if uid not in active_battles:
        active_battles[uid] = start_battle(p, p["floor"])

    state = active_battles[uid]

    await message.answer(
        f"⚔️ БОЙ — этаж {p['floor']}\n\n"
        f"👤 {p['name']}\n"
        f"❤️ Герой: {state['player_hp']} HP\n"
        f"🤖 {state['enemy']['name']}: {state['enemy_hp']} HP\n\n"
        "Выбери действие внизу:",
        reply_markup=battle_keyboard()
    )


@dp.callback_query(lambda c: c.data.startswith("equip_"))
async def equip_action(callback: CallbackQuery):
    uid = callback.from_user.id
    item = callback.data.replace("equip_", "", 1)

    if equip_item(uid, item):
        items = get_inventory(uid)
        equipped = get_equipment(uid)
        await callback.message.answer(
            equipment_text(items, equipped),
            reply_markup=equipment_keyboard(items)
        )
        await callback.answer("Экипировано")
    else:
        await callback.answer("Предмет недоступен", show_alert=True)


@dp.callback_query(lambda c: c.data == "unequip")
async def unequip_action(callback: CallbackQuery):
    uid = callback.from_user.id
    unequip_item(uid)
    items = get_inventory(uid)

    await callback.message.answer(
        equipment_text(items, ""),
        reply_markup=equipment_keyboard(items)
    )
    await callback.answer("Экипировка снята")


async def process_battle_action(uid, message, action):
    p = get_player(uid)

    if not p:
        await message.answer(
            "Сначала выбери героя через /start",
            reply_markup=heroes_keyboard()
        )
        return

    if uid not in active_battles:
        active_battles[uid] = start_battle(p, p["floor"])

    state = active_battles[uid]

    if action == "escape":
        active_battles.pop(uid, None)
        await message.answer(
            "🏃 Побег из боя.",
            reply_markup=main_keyboard()
        )
        return

    state = battle_turn(p, state, action)

    if state["enemy_hp"] <= 0:
        reward = state["enemy"].get("reward", 100)
        add_reward(uid, 100, reward, "iron_sword")
        next_floor(uid)
        active_battles.pop(uid, None)

        await message.answer(
            f"🏆 ПОБЕДА!\n\n"
            f"💰 Награда: +{reward} кредитов\n"
            "⭐ XP: +100\n"
            "⬆️ Следующий этаж открыт.",
            reply_markup=main_keyboard()
        )

    elif state["player_hp"] <= 0:
        active_battles.pop(uid, None)

        await message.answer(
            "💀 ПОРАЖЕНИЕ\n\n"
            "Герой восстановится перед следующим боем.",
            reply_markup=main_keyboard()
        )

    else:
        await message.answer(
            f"⚔️ БОЙ ПРОДОЛЖАЕТСЯ\n\n"
            f"❤️ Герой: {state['player_hp']} HP\n"
            f"🤖 Враг: {state['enemy_hp']} HP\n\n"
            "Выбери действие внизу:",
            reply_markup=battle_keyboard()
        )


@dp.callback_query(lambda c: c.data.startswith("battle_"))
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
            await message.answer(
                equipment_text(items, equipped),
                reply_markup=equipment_keyboard(items)
            )
        else:
            await message.answer(
                "❌ Этого предмета пока нет в рюкзаке.",
                reply_markup=equipment_keyboard(items)
            )
        return

    if text == "❌ Снять экипировку":
        unequip_item(uid)
        await message.answer(
            equipment_text(items, ""),
            reply_markup=equipment_keyboard(items)
        )
        return

    if text == "🔙 В главное меню":
        await message.answer(
            "🏙️ Главное меню",
            reply_markup=main_keyboard()
        )


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
        await message.answer(
            inventory_text(items),
            reply_markup=main_keyboard()
        )

    elif message.text == "🧙 ГЕРОЙ":
        if p:
            await message.answer(
                f"🧙 ГЕРОЙ\n\n"
                f"❤️ HP: {p['hp']}\n"
                f"⚔️ Урон: {p['damage']}\n"
                f"🛡 Броня: {p['armor']}\n"
                f"🏰 Этаж: {p['floor']}\n"
                f"⭐ XP: {p['xp']}\n"
                f"💰 Кредиты: {p['credits']}",
                reply_markup=main_keyboard()
            )
        else:
            await message.answer(
                "Сначала выбери героя через /start",
                reply_markup=heroes_keyboard()
            )

    elif message.text == "🛡 СНАРЯЖЕНИЕ":
        if p:
            items = get_inventory(message.from_user.id)
            equipped = get_equipment(message.from_user.id)
            await message.answer(
                equipment_text(items, equipped),
                reply_markup=equipment_keyboard(items)
            )
        else:
            await message.answer(
                "Сначала выбери героя через /start",
                reply_markup=heroes_keyboard()
            )

    elif message.text == "🏰 БАШНЯ":
        await message.answer(
            f"🏰 БАШНЯ\n\n"
            f"Текущий этаж: {p['floor'] if p else 1}\n"
            "Победи врага, чтобы подняться выше.",
            reply_markup=main_keyboard()
        )

    elif message.text == "🛒 МАГАЗИН":
        await message.answer(
            "🛒 МАГАЗИН\n\n"
            "⚔️ Железный меч — уже доступен\n"
            "🛡 Стальная броня — скоро\n\n"
            "Магазин будет расширяться.",
            reply_markup=main_keyboard()
        )

    elif message.text == "🏆 РЕЙТИНГ":
        await message.answer(
            "🏆 РЕЙТИНГ\n\n"
            "Таблица лидеров будет добавлена следующим обновлением.",
            reply_markup=main_keyboard()
        )


async def main():
    init_db()
    await bot.set_my_commands([
        BotCommand(command="start", description="🎮 Запуск")
    ])
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
