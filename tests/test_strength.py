import unittest

from app.strength import evaluate_strength


class PasswordStrengthTests(unittest.TestCase):
    def test_empty_password_is_weak(self) -> None:
        self.assertEqual(evaluate_strength("").label, "WEAK")

    def test_strength_increases_with_length_and_variety(self) -> None:
        short = evaluate_strength("abcd")
        long = evaluate_strength("aB7!xQ2#mN9@rT4$")
        self.assertEqual(short.label, "WEAK")
        self.assertEqual(long.label, "STRONG")
        self.assertGreater(long.entropy_bits, short.entropy_bits)

    def test_medium_strength_estimate(self) -> None:
        result = evaluate_strength("abcdefghijkl")
        self.assertEqual(result.label, "MEDIUM")

    def test_non_string_password_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_strength(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
