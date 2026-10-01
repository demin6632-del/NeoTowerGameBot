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
        return "🎒 Рюкзак пуст\n\nНайди предметы в башне или купи их в магазине."

    result = "🎒 РЮКЗАК\n\n"
    total_damage = 0
    total_armor = 0

    for item in items:
        data = ITEMS.get(item)
        if data:
            result += f"• {data['name']}\n"
            total_damage += data.get("damage", 0)
            total_armor += data.get("armor", 0)

    result += "\n📊 Бонусы предметов:\n"
    result += f"⚔️ Урон: +{total_damage}\n"
    result += f"🛡 Броня: +{total_armor}"

    return result


def equipment_text(items, equipped=""):
    weapon = "нет"
    armor = "нет"

    for item in items:
        data = ITEMS.get(item)
        if not data:
            continue
        if data.get("type") == "weapon" and item == equipped:
            weapon = data["name"]
        if data.get("type") == "armor" and item == equipped:
            armor = data["name"]

    if equipped and weapon == "нет" and armor == "нет":
        equipped_data = ITEMS.get(equipped)
        if equipped_data:
            if equipped_data.get("type") == "weapon":
                weapon = equipped_data["name"]
            elif equipped_data.get("type") == "armor":
                armor = equipped_data["name"]

    return (
        "🛡 СНАРЯЖЕНИЕ\n\n"
        f"⚔️ Оружие: {weapon}\n"
        f"🛡 Броня: {armor}\n\n"
        "Выбери предмет для экипировки."
    )
