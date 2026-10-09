import unittest

from battle import battle_turn, get_equipment_armor_bonus, get_equipment_bonus


class BattleActionValidationTests(unittest.TestCase):
    def setUp(self):
        self.player = {
            "hp": 200,
            "damage": 30,
            "armor": 20,
            "equipment": "iron_sword,steel_armor",
        }
        self.state = {
            "enemy": {"name": "Test enemy", "hp": 100, "damage": 12, "reward": 10},
            "player_hp": 200,
            "enemy_hp": 100,
            "log": [],
        }

    def test_equipment_bonuses_are_applied(self):
        self.assertEqual(get_equipment_bonus(self.player), 10)
        self.assertEqual(get_equipment_armor_bonus(self.player), 10)

    def test_unknown_action_is_rejected_without_mutating_battle(self):
        before = {
            "player_hp": self.state["player_hp"],
            "enemy_hp": self.state["enemy_hp"],
            "log": list(self.state["log"]),
        }
        with self.assertRaises(ValueError):
            battle_turn(self.player, self.state, "teleport")
        self.assertEqual(self.state["player_hp"], before["player_hp"])
        self.assertEqual(self.state["enemy_hp"], before["enemy_hp"])
        self.assertEqual(self.state["log"], before["log"])

    def test_defend_consumes_exactly_one_enemy_turn(self):
        state = battle_turn(self.player, self.state, "defend")
        self.assertEqual(state["enemy_hp"], 100)
        self.assertLess(state["player_hp"], 200)
        self.assertEqual(len(state["log"]), 1)
        self.assertIn("Защита", state["log"][0])


if __name__ == "__main__":
    unittest.main()
