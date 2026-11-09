"""Cryptographically secure password generation."""

import secrets
import string
from collections.abc import Iterable

from app.config import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH

CATEGORY_POOLS = {
    "uppercase": string.ascii_uppercase,
    "lowercase": string.ascii_lowercase,
    "numbers": string.digits,
    "symbols": "!@#$%^&*()-_=+[]{};:,.?/|~",
}
AMBIGUOUS_CHARACTERS = frozenset("0O1lI")
SUPPORTED_CATEGORIES = frozenset(CATEGORY_POOLS)


def get_character_pools(exclude_ambiguous: bool = False) -> dict[str, str]:
    """Return category pools, optionally removing visually ambiguous characters."""
    if not isinstance(exclude_ambiguous, bool):
        raise ValueError("The ambiguous-character option must be a boolean.")

    pools = dict(CATEGORY_POOLS)
    if exclude_ambiguous:
        pools = {
            category: "".join(
                character
                for character in characters
                if character not in AMBIGUOUS_CHARACTERS
            )
            for category, characters in pools.items()
        }
    return pools


def generate_password(
    length: int,
    categories: Iterable[str],
    exclude_ambiguous: bool = False,
) -> str:
    """Generate a password containing at least one character from each category."""
    if isinstance(length, bool) or not isinstance(length, int):
        raise ValueError("Password length must be a whole number.")
    if not MIN_PASSWORD_LENGTH <= length <= MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Password length must be between {MIN_PASSWORD_LENGTH} "
            f"and {MAX_PASSWORD_LENGTH} characters."
        )

    try:
        selected = tuple(dict.fromkeys(categories))
    except TypeError as error:
        raise ValueError("Character categories must be provided as a collection.") from error
    if not selected:
        raise ValueError("Select at least two character categories.")
    unknown = [category for category in selected if category not in SUPPORTED_CATEGORIES]
    if unknown:
        raise ValueError(f"Unsupported character category: {unknown[0]!r}.")
    if len(selected) < 2:
        raise ValueError("Select at least two character categories.")
    if len(selected) > length:
        raise ValueError("Password length must fit every selected category.")

    pools = get_character_pools(exclude_ambiguous)
    for category in selected:
        if not pools[category]:
            raise ValueError(f"The {category} character pool is empty.")

    characters = [secrets.choice(pools[category]) for category in selected]
    combined_pool = "".join(pools[category] for category in selected)
    characters.extend(
        secrets.choice(combined_pool) for _ in range(length - len(characters))
    )
    secrets.SystemRandom().shuffle(characters)
    return "".join(characters)
