import random

from tower import TOWER


def create_enemy(floor):
    return TOWER.get(floor, TOWER[1]).copy()


def attack(damage):
    return damage + random.randint(-5, 5)


def enemy_attack(enemy_damage, armor):
    return max(enemy_damage - armor, 1)
