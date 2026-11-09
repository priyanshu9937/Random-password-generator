import unittest

from app.generator import (
    AMBIGUOUS_CHARACTERS,
    generate_password,
)


class PasswordGeneratorTests(unittest.TestCase):
    def test_password_has_requested_length(self) -> None:
        password = generate_password(32, ["uppercase", "lowercase"])
        self.assertEqual(len(password), 32)

    def test_selected_categories_are_represented(self) -> None:
        cases = {
            "uppercase": lambda char: char.isupper(),
            "lowercase": lambda char: char.islower(),
            "numbers": lambda char: char.isdigit(),
            "symbols": lambda char: not char.isalnum(),
        }
        selected = tuple(cases)
        password = generate_password(64, selected)
        for category in selected:
            self.assertTrue(any(cases[category](char) for char in password))

    def test_ambiguous_characters_are_excluded(self) -> None:
        password = generate_password(
            128,
            ["uppercase", "lowercase", "numbers", "symbols"],
            exclude_ambiguous=True,
        )
        self.assertTrue(AMBIGUOUS_CHARACTERS.isdisjoint(password))

    def test_minimum_and_maximum_lengths_are_valid(self) -> None:
        for length in (8, 128):
            with self.subTest(length=length):
                self.assertEqual(
                    len(generate_password(length, ["uppercase", "lowercase"])),
                    length,
                )

    def test_out_of_range_lengths_are_rejected(self) -> None:
        for length in (7, 129):
            with self.subTest(length=length), self.assertRaises(ValueError):
                generate_password(length, ["uppercase", "lowercase"])

    def test_invalid_category_selection_is_rejected(self) -> None:
        for categories in ([], ["uppercase"], ["uppercase", "unknown"]):
            with self.subTest(categories=categories), self.assertRaises(ValueError):
                generate_password(16, categories)

    def test_non_integer_length_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            generate_password(16.5, ["uppercase", "lowercase"])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
