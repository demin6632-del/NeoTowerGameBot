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
    """Показывает экипируемые предметы; расходники остаются в рюкзаке."""
    rows = []
    labels = {
        "iron_sword": "⚔️ Железный меч",
        "steel_armor": "🛡 Стальная броня",
    }
    for item in items:
        label = labels.get(item)
        if label:
            rows.append([InlineKeyboardButton(text=label, callback_data=f"equip_{item}")])

    rows.append([InlineKeyboardButton(text="❌ Снять экипировку", callback_data="unequip")])
    rows.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="equipment_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
