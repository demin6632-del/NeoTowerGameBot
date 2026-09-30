from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏰 БАШНЯ"), KeyboardButton(text="⚔️ БОЙ")],
            [KeyboardButton(text="🧙 ГЕРОЙ"), KeyboardButton(text="🎒 РЮКЗАК")],
            [KeyboardButton(text="🛡 СНАРЯЖЕНИЕ")],
            [KeyboardButton(text="🛒 МАГАЗИН"), KeyboardButton(text="🏆 РЕЙТИНГ")]
        ],
        resize_keyboard=True
    )


def heroes_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 КИБОРГ", callback_data="hero_cyborg")],
        [InlineKeyboardButton(text="🥷 НИНДЗЯ", callback_data="hero_ninja")],
        [InlineKeyboardButton(text="🔮 ПСИОНИК", callback_data="hero_psionic")]
    ])


def battle_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ АТАКА", callback_data="battle_attack")],
        [InlineKeyboardButton(text="🛡 ЗАЩИТА", callback_data="battle_defend")],
        [InlineKeyboardButton(text="💊 ЗЕЛЬЕ", callback_data="battle_potion")],
        [InlineKeyboardButton(text="🏃 ПОБЕГ", callback_data="battle_escape")]
    ])
