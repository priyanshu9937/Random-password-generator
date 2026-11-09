"""Educational password-strength estimates."""

from dataclasses import dataclass
import math
import string


@dataclass(frozen=True)
class StrengthResult:
    label: str
    score: int
    entropy_bits: float
    message: str
    color: str


def evaluate_strength(password: str) -> StrengthResult:
    """Estimate strength from password length and the character sets it uses.

    This is an educational estimate, not a formal security assessment.
    """
    if not isinstance(password, str):
        raise ValueError("Password must be text.")
    if not password:
        return StrengthResult(
            label="WEAK",
            score=0,
            entropy_bits=0.0,
            message="Generate a password to see an educational estimate.",
            color="#EF4444",
        )

    alphabet_size = 0
    categories = (
        string.ascii_lowercase,
        string.ascii_uppercase,
        string.digits,
        string.punctuation,
    )
    for category in categories:
        if any(character in category for character in password):
            alphabet_size += len(category)

    entropy_bits = len(password) * math.log2(max(alphabet_size, 1))
    score = min(100, round(entropy_bits))
    if entropy_bits < 40:
        label, color = "WEAK", "#EF4444"
        message = "Consider a longer password and more character variety."
    elif entropy_bits < 70:
        label, color = "MEDIUM", "#F59E0B"
        message = "A good start; additional length can improve this estimate."
    else:
        label, color = "STRONG", "#10B981"
        message = "Strong estimate. Keep it unique and store it safely."

    return StrengthResult(
        label=label,
        score=score,
        entropy_bits=round(entropy_bits, 1),
        message=message,
        color=color,
    )
