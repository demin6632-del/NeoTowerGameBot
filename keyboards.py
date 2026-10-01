from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚔️ БОЙ"), KeyboardButton(text="🏰 БАШНЯ")],
            [KeyboardButton(text="🧙 ГЕРОЙ"), KeyboardButton(text="🛡 СНАРЯЖЕНИЕ")],
            [KeyboardButton(text="🎒 РЮКЗАК"), KeyboardButton(text="🛒 МАГАЗИН")],
            [KeyboardButton(text="🏆 РЕЙТИНГ")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие..."
    )


def heroes_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 КИБОРГ", callback_data="hero_cyborg")],
        [InlineKeyboardButton(text="🥷 НИНДЗЯ", callback_data="hero_ninja")],
        [InlineKeyboardButton(text="🔮 ПСИОНИК", callback_data="hero_psionic")]
    ])


def battle_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚔️ АТАКА"), KeyboardButton(text="🛡 ЗАЩИТА")],
            [KeyboardButton(text="💊 ЗЕЛЬЕ"), KeyboardButton(text="🏃 ПОБЕГ")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие в бою..."
    )


def equipment_keyboard(items):
    rows = []
    for item in items:
        label = {
            "iron_sword": "⚔️ Железный меч",
            "steel_armor": "🛡 Стальная броня"
        }.get(item, f"⚙️ {item.replace('_', ' ')}")
        rows.append([KeyboardButton(text=f"⚙️ {label}")])

    rows.append([KeyboardButton(text="❌ Снять экипировку")])
    rows.append([KeyboardButton(text="🔙 В главное меню")])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выбери предмет..."
    )
