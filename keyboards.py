from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏢 Башня", callback_data="tower")],
            [InlineKeyboardButton(text="👤 Герой", callback_data="profile")]
        ]
    )


def heroes_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Киборг", callback_data="hero_cyborg")],
            [InlineKeyboardButton(text="🥷 Ниндзя", callback_data="hero_ninja")],
            [InlineKeyboardButton(text="🔮 Псионик", callback_data="hero_psionic")]
        ]
    )
