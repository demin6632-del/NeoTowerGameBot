import random

from tower import TOWER


def create_enemy(floor):
    """Return a normalized enemy record for the selected tower floor."""
    source = TOWER.get(floor, TOWER[max(TOWER.keys())])
    enemy = source.copy()
    enemy["floor_name"] = source.get("name", f"Этаж {floor}")
    enemy["name"] = source.get("enemy", source.get("name", "Неизвестный враг"))
    return enemy


def get_equipment_bonus(player):
    equipment = player["equipment"] if "equipment" in player.keys() else ""
    bonus = 0

    for item in (equipment or "").split(","):
        if item == "iron_sword":
            bonus += 10

    return bonus


def get_equipment_armor_bonus(player):
    equipment = player["equipment"] if "equipment" in player.keys() else ""
    bonus = 0

    for item in (equipment or "").split(","):
        if item == "steel_armor":
            bonus += 10

    return bonus


def player_attack(damage, bonus=0):
    return max(damage + bonus + random.randint(-5, 10), 1)


def enemy_attack(enemy_damage, armor):
    return max(enemy_damage - armor, 1)


def start_battle(player, floor):
    enemy = create_enemy(floor)
    return {
        "enemy": enemy,
        "player_hp": player["hp"],
        "enemy_hp": enemy["hp"],
        "log": []
    }


def battle_turn(player, state, action):
    if action not in {"attack", "defend", "potion"}:
        raise ValueError(f"Unsupported battle action: {action!r}")

    attack_bonus = get_equipment_bonus(player)
    armor_bonus = get_equipment_armor_bonus(player)
    effective_armor = player["armor"] + armor_bonus
    log = state["log"]

    if action == "attack":
        damage = player_attack(player["damage"], attack_bonus)
        state["enemy_hp"] = max(0, state["enemy_hp"] - damage)
        log.append(f"⚔️ Ты нанёс {damage} урона")

    elif action == "defend":
        damage = max(enemy_attack(state["enemy"]["damage"], effective_armor) // 2, 1)
        state["player_hp"] = max(0, state["player_hp"] - damage)
        log.append(f"🛡 Защита! Получено {damage} урона")

    elif action == "potion":
        max_hp = player["hp"]
        old_hp = state["player_hp"]
        state["player_hp"] = min(max_hp, old_hp + 30)
        log.append(f"💊 Восстановлено {state['player_hp'] - old_hp} HP")

    if action != "defend" and state["enemy_hp"] > 0:
        damage = enemy_attack(state["enemy"]["damage"], effective_armor)
        state["player_hp"] = max(0, state["player_hp"] - damage)
        log.append(f"🤖 Враг нанёс {damage} урона")
    elif action == "defend":
        # Defend already includes the enemy's attack at half damage.
        pass

    return state


def fight(player, floor):
    state = start_battle(player, floor)

    while state["player_hp"] > 0 and state["enemy_hp"] > 0:
        state = battle_turn(player, state, "attack")

    return {
        "win": state["player_hp"] > 0,
        "hp": state["player_hp"],
        "reward": state["enemy"].get("reward", 0) if state["player_hp"] > 0 else 0,
        "log": state["log"]
    }
