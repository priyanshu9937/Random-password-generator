import unittest

from app.history import PasswordHistory


class PasswordHistoryTests(unittest.TestCase):
    def test_history_keeps_only_the_latest_five(self) -> None:
        history = PasswordHistory()
        for number in range(7):
            history.add(f"password-{number}")
        self.assertEqual(len(history.entries), 5)
        self.assertEqual(
            [entry.password for entry in history.entries],
            [f"password-{number}" for number in range(6, 1, -1)],
        )

    def test_history_can_be_cleared(self) -> None:
        history = PasswordHistory()
        history.add("temporary")
        history.clear()
        self.assertEqual(history.entries, ())

    def test_empty_password_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PasswordHistory().add("")


if __name__ == "__main__":
    unittest.main()
