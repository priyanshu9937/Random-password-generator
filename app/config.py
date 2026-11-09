"""Application settings and visual theme."""

APP_NAME = "Secure Password Generator"
APP_VERSION = "1.0.0"

COLORS = {
    "background": "#FFFFFF",
    "sidebar": "#A8EBD6",
    "sidebar_shadow": "#7FD5BC",
    "primary": "#FF8277",
    "primary_hover": "#F66F68",
    "lavender": "#B99AF4",
    "light_lavender": "#D9C9FF",
    "mint": "#A5E8D0",
    "sky": "#A9DDF3",
    "peach": "#FFB895",
    "butter": "#FFE28B",
    "text": "#25243A",
    "secondary_text": "#777586",
    "muted": "#A19FAE",
    "card": "#FFFDFB",
    "border": "#F0EBE8",
    "shadow": "#EAE6E5",
    "shadow_soft": "#F4F1F0",
    "highlight": "#FFFFFF",
    "success": "#63CBA1",
    "warning": "#F2BE62",
    "danger": "#E97068",
}

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
DEFAULT_PASSWORD_LENGTH = 16
MAX_HISTORY_ITEMS = 5

CATEGORY_LABELS = {
    "uppercase": "Uppercase letters",
    "lowercase": "Lowercase letters",
    "numbers": "Numbers",
    "symbols": "Special symbols",
}
