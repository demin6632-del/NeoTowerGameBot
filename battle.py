import random

from tower import TOWER



def create_enemy(floor):
    return TOWER.get(floor, TOWER[1]).copy()



def player_attack(damage):
    return max(damage + random.randint(-5, 10), 1)



def enemy_attack(enemy_damage, armor):
    return max(enemy_damage - armor, 1)



def fight(player, floor):
    enemy = create_enemy(floor)

    player_hp = player["hp"]
    enemy_hp = enemy["hp"]
    log = []

    while player_hp > 0 and enemy_hp > 0:
        damage = player_attack(player["damage"])
        enemy_hp -= damage
        log.append(f"⚔️ Ты нанёс {damage} урона")

        if enemy_hp <= 0:
            break

        damage = enemy_attack(enemy["damage"], player["armor"])
        player_hp -= damage
        log.append(f"🤖 Враг нанёс {damage} урона")

    if player_hp > 0:
        return {
            "win": True,
            "hp": player_hp,
            "reward": enemy.get("credits", 0),
            "log": log
        }

    return {
        "win": False,
        "hp": player_hp,
        "reward": 0,
        "log": log
    }
