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


if __name__ == "__main__":
    unittest.main()
