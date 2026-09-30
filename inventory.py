ITEMS = {
    "iron_sword": {
        "name": "⚔️ Железный меч",
        "type": "weapon",
        "damage": 10
    },
    "steel_armor": {
        "name": "🛡 Стальная броня",
        "type": "armor",
        "armor": 10
    }
}


def starter_inventory():
    return ["iron_sword"]


def get_item(item_id):
    return ITEMS.get(item_id)


def inventory_text(items):
    if not items:
        return "🎒 Инвентарь пуст"

    result = "🎒 Инвентарь:\n\n"

    for item in items:
        data = ITEMS.get(item)
        if data:
            result += f"• {data['name']}\n"

    return result
