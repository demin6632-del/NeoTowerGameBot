from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏰 БАШНЯ", callback_data="tower"),
                InlineKeyboardButton(text="⚔️ БОЙ", callback_data="fight")
            ],
            [
                InlineKeyboardButton(text="🧙 ГЕРОЙ", callback_data="profile"),
                InlineKeyboardButton(text="🎒 РЮКЗАК", callback_data="inventory")
            ],
            [
                InlineKeyboardButton(text="🛡 СНАРЯЖЕНИЕ", callback_data="equipment")
            ],
            [
                InlineKeyboardButton(text="🛒 МАГАЗИН", callback_data="shop"),
                InlineKeyboardButton(text="🏆 РЕЙТИНГ", callback_data="rating")
            ]
        ]
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
