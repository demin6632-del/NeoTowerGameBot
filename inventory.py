ITEMS = {
    "iron_sword": {"name": "⚔️ Железный меч", "type": "weapon", "damage": 10},
    "steel_armor": {"name": "🛡 Стальная броня", "type": "armor", "armor": 10},
    "health_potion": {"name": "💊 Зелье здоровья", "type": "consumable", "heal": 30}
}

def starter_inventory():
    return ["iron_sword"]

def get_item(item_id):
    return ITEMS.get(item_id)

def inventory_text(items):
    if not items:
        return "🎒 Рюкзак пуст\n\nНайди предметы в башне или купи их в магазине."

    counts = {}
    for item in items:
        if item in ITEMS:
            counts[item] = counts.get(item, 0) + 1

    result = "🎒 РЮКЗАК\n\n"
    for item, count in counts.items():
        data = ITEMS[item]
        suffix = f" ×{count}" if count > 1 else ""
        result += f"• {data['name']}{suffix}\n"

    result += "\n📦 Всего предметов: " + str(sum(counts.values()))
    return result

def equipment_text(items, equipped=""):
    equipped_set = {x for x in (equipped or "").split(",") if x}
    weapon = "нет"
    armor = "нет"
    for item in items:
        data = ITEMS.get(item)
        if not data or item not in equipped_set:
            continue
        if data.get("type") == "weapon":
            weapon = data["name"]
        elif data.get("type") == "armor":
            armor = data["name"]
    return (
        "🛡 СНАРЯЖЕНИЕ\n\n"
        f"⚔️ Оружие: {weapon}\n"
        f"🛡 Броня: {armor}\n\n"
        "Выбери предмет для экипировки."
    )
