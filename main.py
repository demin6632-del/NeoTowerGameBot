import asyncio
import hashlib
import os
from pathlib import Path

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BotCommand, Update

from config import BOT_TOKEN
from database import (
    init_db, get_player, create_player, add_reward, next_floor,
    get_inventory, get_equipment, equip_item, unequip_item,
    get_battle_session, save_battle_session, delete_battle_session,
    add_item, remove_item, spend_credits, get_daily_claim, set_daily_claim, claim_daily_reward, complete_tower, top_players
)
from keyboards import (
    heroes_keyboard, main_keyboard, battle_keyboard, equipment_keyboard
)
from heroes import HEROES
from inventory import inventory_text, equipment_text, ITEMS
from battle import start_battle, battle_turn
from tower import MAX_FLOOR
from error_handler import setup_error_handler

active_battles = {}

IMAGE_URLS = {
    "home": "https://r2.starryai.com/results/1056204224/aa887581-c00b-48d8-8b56-f1b15fe2b24f.webp",
    "hero": "https://pbs.twimg.com/media/HCRjaDMXUAAtISe.jpg",
    "tower": "https://r2.starryai.com/results/1056204224/aa887581-c00b-48d8-8b56-f1b15fe2b24f.webp",
    "shop": "https://r2.starryai.com/results/1020109006/e7698c03-8f8a-46aa-8b83-677750a84579.webp",
    "battle": "https://static.wixstatic.com/media/2e8295_6c619453bed94c269a2f4cd6fd448a41~mv2.png/v1/fill/w_1024,h_1024,al_c/2e8295_6c619453bed94c269a2f4cd6fd448a41~mv2.png",
    "backpack": "https://r2.starryai.com/results/1020109006/e7698c03-8f8a-46aa-8b83-677750a84579.webp",
    "equipment": "https://img.2game.info/webp/l/skyrimspecialedition/images/mod/52462/1626474309.jpeg",
}

def image_for_text(text: str) -> str | None:
    t = text.upper()
    # Не прикрепляем случайную универсальную картинку к бою:
    # изображение должно соответствовать конкретному врагу/этажу.
    # Пока персональные изображения врагов не добавлены в assets,
    # лучше показать боевой экран без неверной фотографии.
    if any(marker in t for marker in ("БОЙ", "ВРАГ", "ПОБЕДА", "ПОРАЖЕНИЕ", "АВТО-БОЙ")):
        return None
    if "ГЕРОЙ" in t or "ВЫБЕРИ ГЕРОЯ" in t:
        return IMAGE_URLS["hero"]
    if "БАШНЯ" in t or "ЭТАЖ" in t:
        return IMAGE_URLS["tower"]
    if "МАГАЗИН" in t:
        return IMAGE_URLS["shop"]
    if "РЮКЗАК" in t:
        return IMAGE_URLS["backpack"]
    if "СНАРЯЖЕНИЕ" in t or "ЭКИПИРОВ" in t:
        return IMAGE_URLS["equipment"]
    return IMAGE_URLS["home"]

WEBHOOK_SECRET = hashlib.sha256(BOT_TOKEN.encode("utf-8")).hexdigest()
WEBHOOK_PATH = "/telegram/" + WEBHOOK_SECRET[:32]


async def health_handler(request: web.Request):
    return web.Response(text="NeoTowerGameBot is alive", content_type="text/plain")


async def telegram_webhook(request: web.Request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        return web.Response(status=403, text="Forbidden")
    try:
        payload = await request.json()
        update = Update.model_validate(payload, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception:
        import logging
        logging.exception("Telegram webhook update failed")
        return web.Response(status=500, text="Update processing failed")
    return web.Response(text="OK")


async def on_startup(app: web.Application):
    init_db()
    await bot.set_my_commands([
        BotCommand(command="start", description="🎮 Запуск"),
        BotCommand(command="help", description="📚 Все команды"),
        BotCommand(command="menu", description="🏙️ Главное меню"),
        BotCommand(command="profile", description="👤 Профиль"),
        BotCommand(command="status", description="📊 Полное состояние"),
        BotCommand(command="stats", description="📈 Характеристики"),
        BotCommand(command="hero", description="🧙 Герой"),
        BotCommand(command="tower", description="🏰 Башня"),
        BotCommand(command="floor", description="🏰 Текущий этаж"),
        BotCommand(command="battle", description="⚔️ Начать бой"),
        BotCommand(command="continue", description="▶️ Продолжить бой"),
        BotCommand(command="attack", description="⚔️ Атака"),
        BotCommand(command="defend", description="🛡 Защита"),
        BotCommand(command="potion", description="💊 Зелье"),
        BotCommand(command="escape", description="🏃 Побег"),
        BotCommand(command="enemy", description="🤖 Текущий враг"),
        BotCommand(command="auto", description="🤖 Авто-бой"),
        BotCommand(command="backpack", description="🎒 Рюкзак"),
        BotCommand(command="inventory", description="📦 Предметы"),
        BotCommand(command="equipment", description="🛡 Экипировка"),
        BotCommand(command="equip", description="⚙️ Экипировать"),
        BotCommand(command="unequip", description="❌ Снять экипировку"),
        BotCommand(command="items", description="📦 Все предметы"),
        BotCommand(command="shop", description="🛒 Магазин"),
        BotCommand(command="buy", description="💳 Купить предмет"),
        BotCommand(command="sell", description="💰 Продать предмет"),
        BotCommand(command="coins", description="💰 Баланс"),
        BotCommand(command="balance", description="💰 Баланс"),
        BotCommand(command="level", description="⭐ Уровень"),
        BotCommand(command="xp", description="✨ Опыт"),
        BotCommand(command="achievements", description="🏆 Достижения"),
        BotCommand(command="rating", description="🏆 Рейтинг"),
        BotCommand(command="top", description="🏆 Топ игроков"),
        BotCommand(command="daily", description="🎁 Ежедневная награда"),
        BotCommand(command="bonus", description="🎁 Бонусы"),
        BotCommand(command="next", description="🎯 Следующее действие"),
        BotCommand(command="guide", description="📖 Гайд"),
        BotCommand(command="settings", description="⚙️ Настройки"),
        BotCommand(command="language", description="🌐 Язык"),
        BotCommand(command="save", description="💾 Сохранить бой"),
        BotCommand(command="about", description="ℹ️ Об игре"),
        BotCommand(command="support", description="🆘 Помощь"),
    ])
    base_url = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not base_url:
        raise RuntimeError("RENDER_EXTERNAL_URL is missing; webhook mode requires the public Render URL")
    await bot.set_webhook(
        url=base_url + WEBHOOK_PATH,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=False,
        allowed_updates=dp.resolve_used_update_types(),
    )


async def on_cleanup(app: web.Application):
    # Do not delete the webhook here: during zero-downtime deploys an old
    # instance could otherwise remove the new instance's webhook.
    await bot.session.close()


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_post(WEBHOOK_PATH, telegram_webhook)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
setup_error_handler(dp)


async def visual_answer(message: Message, text: str, reply_markup=None):
    image_url = image_for_text(text)
    if not image_url:
        await message.answer(text, reply_markup=reply_markup)
        return
    try:
        await message.answer_photo(
            image_url,
            caption=text,
            reply_markup=reply_markup
        )
    except Exception:
        await message.answer(text, reply_markup=reply_markup)


def command_arg(message: Message) -> str:
    parts = (message.text or "").split(maxsplit=1)
    return parts[1].strip().lower() if len(parts) > 1 else ""


def require_player(message: Message):
    return get_player(message.from_user.id)


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "📚 NEO TOWER — КОМАНДЫ\n\n"
        "/start — запустить игру\n/menu — главное меню\n/profile — профиль\n/status — полное состояние\n"
        "/stats — характеристики\n/hero — герой\n/tower — башня\n/floor — этаж\n"
        "/battle — начать бой\n/continue — продолжить бой\n/attack — атака\n/defend — защита\n"
        "/potion — зелье\n/escape — побег\n/enemy — текущий враг\n/auto — авто-бой\n"
        "/backpack — рюкзак\n/inventory — предметы\n/equipment — экипировка\n"
        "/equip <item> — экипировать\n/unequip — снять\n/items — все предметы\n"
        "/shop — магазин\n/buy <item> — купить\n/sell <item> — продать\n"
        "/coins — кредиты\n/balance — баланс\n/level — уровень\n/xp — опыт\n"
        "/achievements — достижения\n/rating — рейтинг\n/top — топ игроков\n"
        "/daily — ежедневная награда\n/bonus — бонусы\n/next — следующее действие\n"
        "/guide — гайд\n/settings — настройки\n/language — язык\n/save — сохранить бой\n"
        "/about — об игре\n/support — помощь"
    )


@dp.message(Command("menu"))
async def menu_command(message: Message):
    await visual_answer(message, "🏙️ Главное меню", main_keyboard())


@dp.message(Command("profile"))
async def profile_command(message: Message):
    p = require_player(message)
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    await visual_answer(message, f"👤 ПРОФИЛЬ\n\nИмя: {p['name']}\nГерой: {p['hero']}\n"
        f"🏰 Этаж: {p['floor']}\n⭐ Уровень: {p['level']}\n✨ XP: {p['xp']}\n💰 Кредиты: {p['credits']}", main_keyboard())


@dp.message(Command("status"))
async def status_command(message: Message):
    p = require_player(message)
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    items = get_inventory(message.from_user.id)
    equipped = get_equipment(message.from_user.id)
    state = active_battles.get(message.from_user.id) or get_battle_session(message.from_user.id)
    battle_text = f"{state['enemy']['name']} — {state['enemy_hp']} HP" if state else "нет"
    await visual_answer(message, f"📊 ПОЛНОЕ СОСТОЯНИЕ\n\n🧙 {p['name']}\n❤️ HP: {p['hp']}\n"
        f"⚔️ Урон: {p['damage']}\n🛡 Броня: {p['armor']}\n🏰 Этаж: {p['floor']}\n"
        f"⭐ Уровень: {p['level']}\n✨ XP: {p['xp']}\n💰 Кредиты: {p['credits']}\n"
        f"🎒 Предметов: {len(items)}\n⚙️ Экипировано: {equipped or 'нет'}\n⚔️ Бой: {battle_text}", main_keyboard())


@dp.message(Command("stats"))
@dp.message(Command("hero"))
async def stats_command(message: Message):
    p = require_player(message)
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    await visual_answer(message, f"🧙 ГЕРОЙ\n\n❤️ HP: {p['hp']}\n⚔️ Урон: {p['damage']}\n"
        f"🛡 Броня: {p['armor']}\n🏰 Этаж: {p['floor']}\n⭐ Уровень: {p['level']}\n✨ XP: {p['xp']}", main_keyboard())


@dp.message(Command("tower"))
@dp.message(Command("floor"))
async def tower_command(message: Message):
    p = require_player(message)
    await visual_answer(message, f"🏰 БАШНЯ\n\nТекущий этаж: {p['floor'] if p else 1}\n"
        "Победи врага, чтобы открыть следующий этаж.", main_keyboard())


@dp.message(Command("battle"))
@dp.message(Command("continue"))
async def battle_command(message: Message):
    await run_fight(message.from_user.id, message)


@dp.message(Command("attack"))
@dp.message(Command("defend"))
@dp.message(Command("potion"))
@dp.message(Command("escape"))
async def battle_command_shortcuts(message: Message):
    cmd = (message.text or "").split()[0].lstrip("/").split("@")[0]
    await process_battle_action(message.from_user.id, message, cmd)


@dp.message(Command("enemy"))
async def enemy_command(message: Message):
    p = require_player(message)
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    state = active_battles.get(message.from_user.id) or get_battle_session(message.from_user.id)
    if not state:
        state = start_battle(p, p["floor"])
    await visual_answer(message, f"🤖 ВРАГ\n\n{state['enemy']['name']}\n❤️ HP: {state['enemy_hp']}\n"
        f"⚔️ Урон: {state['enemy']['damage']}\n🏰 Этаж: {p['floor']}", battle_keyboard())


@dp.message(Command("auto"))
async def auto_command(message: Message):
    p = require_player(message)
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    state = active_battles.get(message.from_user.id) or get_battle_session(message.from_user.id)
    if state is None and p["tower_cleared"]:
        await visual_answer(message, "👑 Башня уже покорена! Все 10 этажей пройдены.", main_keyboard())
        return
    state = state or start_battle(p, p["floor"])
    steps = 0
    while state["player_hp"] > 0 and state["enemy_hp"] > 0 and steps < 500:
        state = battle_turn(p, state, "attack")
        steps += 1
    if state["enemy_hp"] <= 0:
        reward = state["enemy"].get("reward", 100)
        add_reward(message.from_user.id, 100, reward)
        if p["floor"] < MAX_FLOOR:
            next_floor(message.from_user.id)
        else:
            complete_tower(message.from_user.id)
        delete_battle_session(message.from_user.id)
        active_battles.pop(message.from_user.id, None)
        result_text = (
            f"🤖 АВТО-БОЙ\n\n🏆 Победа!\n💰 +{reward} кредитов\n⭐ +100 XP\n"
            + ("👑 Вершина башни покорена!" if p["floor"] >= MAX_FLOOR else "⬆️ Следующий этаж открыт.")
        )
        await visual_answer(message, result_text, main_keyboard())
    else:
        if state["player_hp"] <= 0:
            delete_battle_session(message.from_user.id)
            active_battles.pop(message.from_user.id, None)
            await visual_answer(message, "🤖 АВТО-БОЙ\n\n💀 Поражение.\n❤️ Герой восстановится перед следующим боем.", main_keyboard())
        else:
            save_battle_session(message.from_user.id, state)
            active_battles[message.from_user.id] = state
            await visual_answer(message, f"🤖 АВТО-БОЙ\n\n⏸ Бой не завершён.\n❤️ Осталось: {state['player_hp']} HP\n🤖 Враг: {state['enemy_hp']} HP", battle_keyboard())


@dp.message(Command("backpack"))
@dp.message(Command("inventory"))
async def backpack_command(message: Message):
    await visual_answer(message, inventory_text(get_inventory(message.from_user.id)), main_keyboard())


@dp.message(Command("equipment"))
async def equipment_command(message: Message):
    p = require_player(message)
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    items = get_inventory(message.from_user.id)
    await visual_answer(message, equipment_text(items, get_equipment(message.from_user.id)), equipment_keyboard(items))


@dp.message(Command("equip"))
async def equip_command(message: Message):
    item = command_arg(message).replace("-", "_").replace(" ", "_")
    item = {"меч":"iron_sword","железный_меч":"iron_sword","броня":"steel_armor","стальная_броня":"steel_armor"}.get(item, item)
    if equip_item(message.from_user.id, item):
        await message.answer("⚙️ Экипировано.", reply_markup=equipment_keyboard(get_inventory(message.from_user.id)))
    else:
        await message.answer("❌ Предмет не найден в рюкзаке.")


@dp.message(Command("unequip"))
async def unequip_command(message: Message):
    unequip_item(message.from_user.id)
    await message.answer("❌ Экипировка снята.", reply_markup=equipment_keyboard(get_inventory(message.from_user.id)))


@dp.message(Command("items"))
async def items_command(message: Message):
    lines = []
    for item_id, data in ITEMS.items():
        bonus = f"+{data.get('damage', 0)} урона" if data.get('damage') else f"+{data.get('armor', 0)} брони"
        lines.append(f"• {item_id} — {data['name']} ({bonus})")
    await message.answer("📦 ПРЕДМЕТЫ\n\n" + "\n".join(lines))


@dp.message(Command("shop"))
async def shop_command(message: Message):
    await visual_answer(message, "🛒 МАГАЗИН\n\n🛡 steel_armor — 500 кредитов\n💊 health_potion — 100 кредитов\n\nКупить: /buy steel_armor или /buy health_potion", main_keyboard())


@dp.message(Command("buy"))
async def buy_command(message: Message):
    p = require_player(message)
    item = command_arg(message).replace("-", "_").replace(" ", "_")
    item = {"броня":"steel_armor","стальная_броня":"steel_armor","зелье":"health_potion","зелье_здоровья":"health_potion"}.get(item, item)
    prices = {"steel_armor": 500, "health_potion": 100}
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    if item not in prices:
        await message.answer("❌ Сейчас доступна покупка: steel_armor (500) или health_potion (100).")
        return
    if item != "health_potion" and item in get_inventory(message.from_user.id):
        await message.answer("ℹ️ Этот предмет уже есть в рюкзаке.")
        return
    if not spend_credits(message.from_user.id, prices[item]):
        await message.answer(f"💰 Недостаточно кредитов. Нужно {prices[item]}.")
        return
    add_item(message.from_user.id, item)
    await message.answer(f"🛒 Куплено: {ITEMS[item]['name']} за {prices[item]} кредитов.", reply_markup=main_keyboard())


@dp.message(Command("sell"))
async def sell_command(message: Message):
    p = require_player(message)
    item = command_arg(message).replace("-", "_").replace(" ", "_")
    item = {"броня":"steel_armor","стальная_броня":"steel_armor","зелье":"health_potion","зелье_здоровья":"health_potion"}.get(item, item)
    prices = {"steel_armor": 250, "health_potion": 50}
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    if item not in prices:
        await message.answer("❌ Сейчас можно продать: steel_armor (250) или health_potion (50).")
        return
    if remove_item(message.from_user.id, item):
        add_reward(message.from_user.id, 0, prices[item])
        await message.answer(f"💰 Продано: {ITEMS[item]['name']} за {prices[item]} кредитов.", reply_markup=main_keyboard())
    else:
        await message.answer("❌ Этого предмета нет в рюкзаке.")


@dp.message(Command("coins"))
@dp.message(Command("balance"))
async def balance_command(message: Message):
    p = require_player(message)
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    await message.answer(f"💰 Баланс: {p['credits']} кредитов")


@dp.message(Command("level"))
@dp.message(Command("xp"))
async def level_command(message: Message):
    p = require_player(message)
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    next_xp = p["level"] * 500
    await message.answer(f"⭐ Уровень: {p['level']}\n✨ XP: {p['xp']} / {next_xp}")


@dp.message(Command("achievements"))
async def achievements_command(message: Message):
    p = require_player(message)
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    achievements = [
        ("🥉 Первый этаж", p["floor"] >= 2),
        ("⚔️ Первая победа", p["xp"] >= 100),
        ("🔥 Этаж 10", p["floor"] >= 10),
        ("💰 Богач", p["credits"] >= 1000),
    ]
    await message.answer("🏆 ДОСТИЖЕНИЯ\n\n" + "\n".join(("✅ " if ok else "🔒 ") + name for name, ok in achievements))


@dp.message(Command("rating"))
@dp.message(Command("top"))
async def rating_command(message: Message):
    rows = top_players(10)
    if not rows:
        await message.answer("🏆 Пока нет игроков.")
        return
    await message.answer("🏆 ТОП ИГРОКОВ\n\n" + "\n".join(
        f"{i}. {row['name']} — этаж {row['floor']} • ур. {row['level']} • XP {row['xp']}"
        for i, row in enumerate(rows, 1)
    ))


@dp.message(Command("daily"))
async def daily_command(message: Message):
    p = require_player(message)
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    from datetime import datetime, timezone
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not claim_daily_reward(message.from_user.id, day, 50, 250):
        await message.answer("🎁 Ежедневная награда уже получена сегодня.")
        return
    await message.answer("🎁 Ежедневная награда: +50 XP и +250 кредитов!")


@dp.message(Command("bonus"))
async def bonus_command(message: Message):
    await message.answer("🎁 Бонусы: /daily и награды за победы в башне.")


@dp.message(Command("next"))
async def next_command(message: Message):
    p = require_player(message)
    if not p:
        await message.answer("Сначала выбери героя через /start", reply_markup=heroes_keyboard())
        return
    state = active_battles.get(message.from_user.id) or get_battle_session(message.from_user.id)
    if state and state["enemy_hp"] > 0:
        await message.answer("🎯 Следующее действие: /attack\nВ бою сейчас доступна атака.")
    else:
        if p["tower_cleared"]:
            await message.answer("👑 Башня покорена. Ты прошёл все 10 этажей Neo Tower.")
        else:
            await message.answer("🎯 Следующее действие: /battle\nНачни бой на текущем этаже.")


@dp.message(Command("guide"))
async def guide_command(message: Message):
    await message.answer("📖 ГАЙД\n\n1. Выбери героя.\n2. /battle — бой.\n3. /attack, /defend, /potion.\n4. Победа открывает следующий этаж.\n5. /daily — ежедневная награда.")


@dp.message(Command("settings"))
async def settings_command(message: Message):
    await message.answer("⚙️ НАСТРОЙКИ\n\nЯзык: русский\nУведомления: стандартные.")


@dp.message(Command("language"))
async def language_command(message: Message):
    await message.answer("🌐 Сейчас доступен русский язык.")


@dp.message(Command("save"))
async def save_command(message: Message):
    state = active_battles.get(message.from_user.id)
    if state:
        save_battle_session(message.from_user.id, state)
        await message.answer("💾 Бой сохранён.")
    else:
        await message.answer("ℹ️ Активного боя нет.")


@dp.message(Command("about"))
async def about_command(message: Message):
    await message.answer("🏙️ NEO TOWER\nОдиночная башня с боями, героями, экипировкой и прогрессом.")


@dp.message(Command("support"))
async def support_command(message: Message):
    await message.answer("🆘 Поддержка: опиши проблему и приложи скриншот.")


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
        if p["tower_cleared"]:
            await visual_answer(message, "👑 Башня уже покорена! Все 10 этажей пройдены.", main_keyboard())
            return
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
        if p["tower_cleared"]:
            await visual_answer(message, "👑 Башня уже покорена! Все 10 этажей пройдены.", main_keyboard())
            return
        state = start_battle(p, p["floor"])

    active_battles[uid] = state

    if action == "potion":
        if "health_potion" not in get_inventory(uid):
            await message.answer("❌ Зелий здоровья нет в рюкзаке. Купи его в /shop.")
            return
        if state["player_hp"] >= p["hp"]:
            await message.answer("❤️ HP уже полностью восстановлено.")
            return
        remove_item(uid, "health_potion")

    if action == "escape":
        active_battles.pop(uid, None)
        delete_battle_session(uid)
        await visual_answer(message, "🏃 Побег из боя.", main_keyboard())
        return

    state = battle_turn(p, state, action)
    active_battles[uid] = state

    if state["enemy_hp"] <= 0:
        reward = state["enemy"].get("reward", 100)
        add_reward(uid, 100, reward)
        if p["floor"] < MAX_FLOOR:
            next_floor(uid)
            result_text = (
                f"🏆 ПОБЕДА!\n\n💰 Награда: +{reward} кредитов\n"
                "⭐ XP: +100\n⬆️ Следующий этаж открыт."
            )
        else:
            complete_tower(uid)
            result_text = (
                f"👑 ВЕРШИНА ПОКОРЕНА!\n\n💰 Награда: +{reward} кредитов\n"
                "⭐ XP: +100\n🏰 Ты прошёл все 10 этажей Neo Tower!"
            )
        active_battles.pop(uid, None)
        delete_battle_session(uid)

        await visual_answer(message, result_text, main_keyboard())

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
    if not message.text:
        return
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
            "🛡 Стальная броня — 500 кредитов\n"
            "💊 Зелье здоровья — 100 кредитов\n\n"
            "Купить: /buy steel_armor или /buy health_potion.\n"
            "Продать: /sell steel_armor или /sell health_potion.",
            main_keyboard()
        )

    elif message.text == "🏆 РЕЙТИНГ":
        await visual_answer(
            message,
            "🏆 РЕЙТИНГ\n\n"
            + ("\n".join(f"{i}. {row['name']} — этаж {row['floor']} • ур. {row['level']} • XP {row['xp']}" for i, row in enumerate(top_players(10), 1)) or "Пока нет игроков."),
            main_keyboard()
        )


def main():
    web.run_app(
        create_app(),
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "10000")),
    )


if __name__ == "__main__":
    main()
