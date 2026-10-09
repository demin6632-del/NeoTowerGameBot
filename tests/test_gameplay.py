import os
import tempfile
import unittest

import database
from battle import battle_turn, start_battle
from heroes import HEROES


class GameplayTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_database = database.DATABASE
        database.DATABASE = os.path.join(self.temp_dir.name, "test.db")
        database.init_db()
        hero = HEROES["cyborg"]
        database.create_player(12345, "Tester", "cyborg", hero["hp"], hero["damage"], hero["armor"])

    def tearDown(self):
        database.DATABASE = self.old_database
        self.temp_dir.cleanup()

    def test_enemy_has_display_name_and_floor_name(self):
        player = database.get_player(12345)
        state = start_battle(player, 1)
        self.assertEqual(state["enemy"]["name"], "🤖 Дрон MK-1")
        self.assertEqual(state["enemy"]["floor_name"], "Заброшенный сектор")
        self.assertGreater(state["enemy_hp"], 0)

    def test_combat_health_never_goes_below_zero(self):
        player = database.get_player(12345)
        state = start_battle(player, 1)
        state["enemy_hp"] = 1
        state = battle_turn(player, state, "attack")
        self.assertEqual(state["enemy_hp"], 0)
        self.assertGreaterEqual(state["player_hp"], 0)

    def test_daily_reward_can_only_be_claimed_once_per_day(self):
        self.assertTrue(database.claim_daily_reward(12345, "2026-10-09"))
        self.assertFalse(database.claim_daily_reward(12345, "2026-10-09"))
        player = database.get_player(12345)
        self.assertEqual(player["xp"], 50)
        self.assertEqual(player["credits"], 250)

    def test_tower_completion_is_persisted(self):
        database.complete_tower(12345)
        self.assertEqual(database.get_player(12345)["tower_cleared"], 1)

    def test_level_up_increases_combat_stats(self):
        database.add_reward(12345, 500, 100)
        player = database.get_player(12345)
        self.assertEqual(player["level"], 2)
        self.assertEqual(player["xp"], 500)
        self.assertEqual(player["credits"], 100)
        self.assertEqual(player["hp"], HEROES["cyborg"]["hp"] + 20)
        self.assertEqual(player["damage"], HEROES["cyborg"]["damage"] + 5)
        self.assertEqual(player["armor"], HEROES["cyborg"]["armor"] + 3)

    def test_consumable_cannot_be_equipped(self):
        self.assertTrue(database.add_item(12345, "health_potion"))
        self.assertFalse(database.equip_item(12345, "health_potion"))

    def test_equipment_changes_combat_bonuses(self):
        from battle import get_equipment_bonus, get_equipment_armor_bonus
        self.assertTrue(database.equip_item(12345, "iron_sword"))
        self.assertTrue(database.add_item(12345, "steel_armor"))
        self.assertTrue(database.equip_item(12345, "steel_armor"))
        player = database.get_player(12345)
        self.assertEqual(get_equipment_bonus(player), 10)
        self.assertEqual(get_equipment_armor_bonus(player), 10)

    def test_battle_session_survives_database_reload(self):
        from tower import TOWER
        state = {
            "enemy": {**TOWER[1], "name": TOWER[1]["enemy"], "floor_name": TOWER[1]["name"]},
            "player_hp": 150,
            "enemy_hp": 60,
            "log": ["test"],
        }
        database.save_battle_session(12345, state)
        self.assertEqual(database.get_battle_session(12345), state)

    def test_tower_encounters_are_ordered_and_increasing(self):
        from tower import MAX_FLOOR, TOWER
        self.assertEqual(MAX_FLOOR, 10)
        self.assertEqual(sorted(TOWER), list(range(1, 11)))
        for floor in range(2, MAX_FLOOR + 1):
            self.assertGreater(TOWER[floor]["hp"], TOWER[floor - 1]["hp"])
        self.assertTrue(all(row["damage"] > 0 and row["reward"] > 0 for row in TOWER.values()))

    def test_all_heroes_can_clear_tower_with_equipment_and_supplies(self):
        import random
        from tower import MAX_FLOOR, TOWER

        for index, (hero_key, hero) in enumerate(HEROES.items(), start=1):
            user_id = 20000 + index
            database.create_player(
                user_id, f"Tester{index}", hero_key,
                hero["hp"], hero["damage"], hero["armor"]
            )
            database.add_reward(user_id, 0, 5000)
            self.assertTrue(database.add_item(user_id, "steel_armor"))
            self.assertTrue(database.equip_item(user_id, "steel_armor"))
            for _ in range(30):
                self.assertTrue(database.add_item(user_id, "health_potion"))

            random.seed(100 + index)
            for floor in range(1, MAX_FLOOR + 1):
                player = database.get_player(user_id)
                state = start_battle(player, floor)
                potions_left = len([item for item in database.get_inventory(user_id) if item == "health_potion"])
                turns = 0
                while state["player_hp"] > 0 and state["enemy_hp"] > 0 and turns < 250:
                    if state["player_hp"] <= int(player["hp"] * 0.45) and potions_left:
                        self.assertTrue(database.remove_item(user_id, "health_potion"))
                        potions_left -= 1
                        action = "potion"
                    else:
                        action = "attack"
                    state = battle_turn(player, state, action)
                    turns += 1

                self.assertGreater(
                    state["player_hp"], 0,
                    f"{hero_key} could not survive floor {floor} with armor and 30 potions"
                )
                self.assertEqual(state["enemy_hp"], 0, f"{hero_key} did not clear floor {floor}")
                database.add_reward(user_id, 100 + floor * 25, TOWER[floor]["reward"])
                if floor < MAX_FLOOR:
                    database.next_floor(user_id)
                else:
                    database.complete_tower(user_id)

            self.assertEqual(database.get_player(user_id)["tower_cleared"], 1)


if __name__ == "__main__":
    unittest.main()
