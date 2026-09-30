import random

from tower import TOWER


def create_enemy(floor):
    return TOWER.get(floor, TOWER[1]).copy()


def get_equipment_bonus(player):
    equipment = player["equipment"] if "equipment" in player.keys() else ""
    bonus = 0

    if "sword" in equipment:
        bonus += 10
    if "armor" in equipment:
        bonus += 5

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
    bonus = get_equipment_bonus(player)
    log = state["log"]

    if action == "attack":
        damage = player_attack(player["damage"], bonus)
        state["enemy_hp"] -= damage
        log.append(f"⚔️ Ты нанёс {damage} урона")

    elif action == "defend":
        damage = max(enemy_attack(state["enemy"]["damage"], player["armor"]) // 2, 1)
        state["player_hp"] -= damage
        log.append(f"🛡 Защита! Получено {damage} урона")
        return state

    elif action == "potion":
        heal = 30
        state["player_hp"] += heal
        log.append(f"💊 Восстановлено {heal} HP")

    if state["enemy_hp"] > 0:
        damage = enemy_attack(state["enemy"]["damage"], player["armor"])
        state["player_hp"] -= damage
        log.append(f"🤖 Враг нанёс {damage} урона")

    return state


def fight(player, floor):
    state = start_battle(player, floor)

    while state["player_hp"] > 0 and state["enemy_hp"] > 0:
        state = battle_turn(player, state, "attack")

    return {
        "win": state["player_hp"] > 0,
        "hp": state["player_hp"],
        "reward": state["enemy"].get("credits", 0) if state["player_hp"] > 0 else 0,
        "log": state["log"]
    }
