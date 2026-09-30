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
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 КИБОРГ", callback_data="hero_cyborg")],
            [InlineKeyboardButton(text="🥷 НИНДЗЯ", callback_data="hero_ninja")],
            [InlineKeyboardButton(text="🔮 ПСИОНИК", callback_data="hero_psionic")]
        ]
    )


def battle_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚔️ АТАКОВАТЬ", callback_data="attack")],
            [InlineKeyboardButton(text="🏃 ОТСТУПИТЬ", callback_data="escape")]
        ]
    )
