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
    buttons = []
    for item in items:
        buttons.append([InlineKeyboardButton(
            text=f"⚙️ Экипировать {item.replace('_', ' ')}",
            callback_data=f"equip_{item}"
        )])
    buttons.append([InlineKeyboardButton(text="❌ Снять экипировку", callback_data="unequip")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
