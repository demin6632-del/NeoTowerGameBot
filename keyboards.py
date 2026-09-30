from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
                InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory")
            ],
            [
                InlineKeyboardButton(text="🏰 Башня", callback_data="tower"),
                InlineKeyboardButton(text="⚔️ Бой", callback_data="fight")
            ],
            [
                InlineKeyboardButton(text="🛡 Экипировка", callback_data="equipment")
            ]
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


def battle_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚔️ Атаковать", callback_data="attack")],
            [InlineKeyboardButton(text="🏃 Отступить", callback_data="escape")]
        ]
    )
