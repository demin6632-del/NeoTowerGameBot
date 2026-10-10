import unittest

from keyboards import equipment_keyboard


class EquipmentKeyboardTests(unittest.TestCase):
    def test_consumable_is_not_offered_as_equipment(self):
        keyboard = equipment_keyboard(["iron_sword", "steel_armor", "health_potion"])
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
        ]
        self.assertIn("equip_iron_sword", callbacks)
        self.assertIn("equip_steel_armor", callbacks)
        self.assertNotIn("equip_health_potion", callbacks)

    def test_navigation_buttons_remain_available_with_empty_inventory(self):
        keyboard = equipment_keyboard([])
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
        ]
        self.assertIn("unequip", callbacks)
        self.assertIn("equipment_menu", callbacks)


if __name__ == "__main__":
    unittest.main()
