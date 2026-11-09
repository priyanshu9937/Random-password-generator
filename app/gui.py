"""Pastel claymorphism interface for the Secure Password Generator."""

import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox
from types import TracebackType

import customtkinter as ctk

from app.config import (
    APP_NAME,
    APP_VERSION,
    CATEGORY_LABELS,
    COLORS,
    DEFAULT_PASSWORD_LENGTH,
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
)
from app.generator import generate_password
from app.history import HistoryEntry, PasswordHistory
from app.strength import StrengthResult, evaluate_strength
from app.utils import ClipboardError, copy_to_clipboard

LOGGER = logging.getLogger(__name__)

NAV_ITEMS = (
    ("Dashboard", "⌂"),
    ("Password Generator", "✳"),
    ("Password History", "◷"),
    ("Security Guide", "◇"),
    ("Settings", "⚙"),
    ("About", "i"),
)

CATEGORY_STYLES = {
    "uppercase": ("Aa", COLORS["lavender"], "Add capital letters"),
    "lowercase": ("ab", COLORS["mint"], "Keep it easy to read"),
    "numbers": ("09", COLORS["sky"], "Mix in a few digits"),
    "symbols": ("!?", COLORS["peach"], "Add special characters"),
}

STRENGTH_COLORS = {
    "WEAK": COLORS["primary"],
    "MEDIUM": COLORS["warning"],
    "STRONG": COLORS["success"],
}


class PasswordGeneratorApp:
    """Owns the app window, view state, and interactions."""

    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1200x800")
        self.root.minsize(940, 680)
        self.root.configure(fg_color=COLORS["background"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.report_callback_exception = self._report_callback_exception

        self.history = PasswordHistory()
        self.current_password = tk.StringVar(value="")
        self.password_visible = tk.BooleanVar(value=True)
        self.exclude_ambiguous = tk.BooleanVar(value=False)
        self.length = tk.IntVar(value=DEFAULT_PASSWORD_LENGTH)
        self.category_vars = {
            "uppercase": tk.BooleanVar(value=True),
            "lowercase": tk.BooleanVar(value=True),
            "numbers": tk.BooleanVar(value=True),
            "symbols": tk.BooleanVar(value=True),
        }
        self._history_visibility: dict[int, bool] = {}
        self._active_page = "Dashboard"

        self._build_shell()
        self._show_page(self._active_page)

    def _build_shell(self) -> None:
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        sidebar_shadow = ctk.CTkFrame(
            self.root,
            width=212,
            corner_radius=26,
            fg_color=COLORS["sidebar_shadow"],
            border_width=0,
        )
        sidebar_shadow.grid(row=0, column=0, sticky="nsew", padx=(13, 0), pady=14)
        self.sidebar = ctk.CTkFrame(
            sidebar_shadow,
            corner_radius=25,
            fg_color=COLORS["sidebar"],
            border_width=1,
            border_color=COLORS["highlight"],
        )
        self.sidebar.place(x=0, y=0, relwidth=1, relheight=1)

        self.main_area = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_area.grid(
            row=0, column=1, sticky="nsew", padx=(25, 30), pady=(25, 20)
        )
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(1, weight=1)

        self._build_sidebar()
        self._build_header()
        self.page = ctk.CTkScrollableFrame(
            self.main_area,
            fg_color="transparent",
            scrollbar_button_color=COLORS["shadow"],
            scrollbar_button_hover_color=COLORS["lavender"],
        )
        self.page.grid(row=1, column=0, sticky="nsew", pady=(17, 0))
        self.page.grid_columnconfigure(0, weight=1)

    def _build_sidebar(self) -> None:
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=17, pady=(23, 24))
        logo_shadow = ctk.CTkFrame(
            brand,
            width=46,
            height=46,
            corner_radius=16,
            fg_color=COLORS["primary_hover"],
        )
        logo_shadow.pack(side="left", padx=(0, 10), pady=(2, 0))
        logo = ctk.CTkFrame(
            logo_shadow,
            width=46,
            height=46,
            corner_radius=16,
            fg_color=COLORS["primary"],
            border_width=1,
            border_color=COLORS["highlight"],
        )
        logo.place(x=0, y=0, relwidth=1, relheight=1)
        logo.pack_propagate(False)
        self._draw_lock_icon(logo, size=46, compact=True)

        identity = ctk.CTkFrame(brand, fg_color="transparent")
        identity.pack(side="left", fill="y")
        ctk.CTkLabel(
            identity,
            text="Securely.",
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", pady=(3, 0))
        ctk.CTkLabel(
            identity,
            text="PASSWORD STUDIO",
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color=COLORS["secondary_text"],
        ).pack(anchor="w", pady=(1, 0))

        ctk.CTkLabel(
            self.sidebar,
            text="YOUR WORKSPACE",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=COLORS["secondary_text"],
        ).pack(anchor="w", padx=19, pady=(0, 9))

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        for label, icon in NAV_ITEMS:
            button = ctk.CTkButton(
                self.sidebar,
                text=f"{icon}   {label}",
                anchor="w",
                height=41,
                corner_radius=14,
                border_width=1,
                border_color=COLORS["sidebar"],
                fg_color="transparent",
                hover_color=COLORS["mint"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda selected=label: self._on_navigation(selected),
            )
            button.pack(fill="x", padx=9, pady=3)
            self.nav_buttons[label] = button

        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(expand=True, fill="both")
        note_wrapper, security_note = self._clay_card(
            self.sidebar,
            "Made for your peace of mind",
            "Passwords stay on this device and in this session only.",
            height=126,
            color=COLORS["card"],
            shadow=COLORS["sidebar_shadow"],
            radius=19,
            description_width=150,
        )
        note_wrapper.pack(fill="x", padx=11, pady=(0, 14))
        ctk.CTkLabel(
            security_note,
            text="●  PRIVATE & LOCAL",
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", pady=(5, 0))

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="YOUR PERSONAL PASSWORD WORKSHOP",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=COLORS["secondary_text"],
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.header_title = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text"],
            justify="left",
        )
        self.header_title.grid(row=1, column=0, sticky="w")
        self.header_description = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["secondary_text"],
            justify="left",
        )
        self.header_description.grid(row=2, column=0, sticky="w", pady=(3, 0))
        self.notification = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=COLORS["success"],
            anchor="w",
        )
        self.notification.grid(row=3, column=0, sticky="w", pady=(3, 0))

        badge_shadow = ctk.CTkFrame(
            header,
            corner_radius=14,
            fg_color=COLORS["sidebar_shadow"],
            border_width=0,
        )
        badge_shadow.grid(row=0, column=1, rowspan=4, sticky="e", pady=(3, 0))
        badge = ctk.CTkFrame(
            badge_shadow,
            corner_radius=14,
            fg_color=COLORS["mint"],
            border_width=1,
            border_color=COLORS["highlight"],
        )
        badge.pack(padx=(0, 2), pady=(0, 3))
        ctk.CTkLabel(
            badge,
            text="●  SECURE SESSION",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=12, pady=8)

    def _clay_card(
        self,
        parent: ctk.CTkBaseClass,
        title: str,
        description: str | None = None,
        *,
        height: int = 170,
        color: str | None = None,
        shadow: str | None = None,
        radius: int = 22,
        heading_color: str | None = None,
        description_width: int = 620,
    ) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
        """Build one raised pastel panel from a single offset shadow and face."""
        wrapper = ctk.CTkFrame(parent, fg_color="transparent", height=height)
        wrapper.grid_propagate(False)
        ctk.CTkFrame(
            wrapper,
            corner_radius=radius,
            fg_color=shadow or COLORS["shadow"],
            border_width=0,
        ).place(x=3, y=5, relwidth=1, relheight=1)
        face = ctk.CTkFrame(
            wrapper,
            corner_radius=radius,
            fg_color=color or COLORS["card"],
            border_width=1,
            border_color=COLORS["highlight"],
        )
        face.place(x=0, y=0, relwidth=1, relheight=1)
        ctk.CTkLabel(
            face,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=heading_color or COLORS["text"],
        ).pack(anchor="w", padx=16, pady=(13, 0))
        if description:
            ctk.CTkLabel(
                face,
                text=description,
                font=ctk.CTkFont(size=9),
                text_color=COLORS["secondary_text"],
                wraplength=description_width,
                justify="left",
            ).pack(anchor="w", padx=16, pady=(2, 0))
        body = ctk.CTkFrame(face, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=13, pady=(7, 11))
        return wrapper, body

    def _clay_button(
        self,
        parent: ctk.CTkBaseClass,
        text: str,
        command: Callable[[], None],
        *,
        tone: str = "coral",
        width: int = 112,
        height: int = 38,
    ) -> ctk.CTkButton:
        tones = {
            "coral": (COLORS["primary"], COLORS["primary_hover"], COLORS["text"]),
            "lavender": (
                COLORS["light_lavender"],
                COLORS["lavender"],
                COLORS["text"],
            ),
            "mint": (COLORS["mint"], COLORS["sidebar_shadow"], COLORS["text"]),
            "white": (COLORS["card"], COLORS["light_lavender"], COLORS["text"]),
            "warning": (COLORS["butter"], COLORS["butter"], COLORS["text"]),
        }
        color, hover, foreground = tones[tone]
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            corner_radius=15,
            border_width=1,
            border_color=COLORS["highlight"],
            fg_color=color,
            hover_color=hover,
            text_color=foreground,
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        return button

    def _on_navigation(self, label: str) -> None:
        if label == "Settings":
            self._show_page("Settings")
        elif label in ("Dashboard", "Password Generator"):
            self._show_page(label)
        elif label == "Password History":
            self._show_page("Password History")
        elif label in ("Security Guide", "About"):
            self._show_page(label)

    def _show_page(self, page_name: str) -> None:
        page_copy = {
            "Dashboard": (
                "A safer little corner of the internet.",
                "Make a long, unique password without sending it anywhere.",
            ),
            "Password Generator": (
                "Your Password Studio",
                "Create strong, unique and secure passwords in seconds.",
            ),
            "Password History": (
                "Recently Generated",
                "Your latest passwords, kept in memory for this session only.",
            ),
            "Security Guide": (
                "Small habits, stronger accounts.",
                "Friendly reminders for keeping your online accounts safer.",
            ),
            "Settings": (
                "Make it your own.",
                "Set a comfortable length and choose your character mix.",
            ),
            "About": (
                "Securely, thoughtfully made.",
                "A private desktop password generator built around secure randomness.",
            ),
        }
        if page_name not in page_copy:
            raise ValueError(f"Unknown application page: {page_name}")

        self._active_page = page_name
        selected_nav = (
            "Password History" if page_name == "Password History" else page_name
        )
        for label, button in self.nav_buttons.items():
            active = label == selected_nav
            button.configure(
                fg_color=COLORS["primary"] if active else "transparent",
                hover_color=COLORS["primary_hover"] if active else COLORS["mint"],
                border_color=COLORS["primary_hover"] if active else COLORS["sidebar"],
                text_color=COLORS["highlight"] if active else COLORS["text"],
            )

        title, description = page_copy[page_name]
        self.header_title.configure(text=title)
        self.header_description.configure(text=description)
        for child in self.page.winfo_children():
            child.destroy()

        for column in range(4):
            self.page.grid_columnconfigure(column, weight=1, uniform="page")
        if page_name in ("Dashboard", "Password Generator"):
            self._render_generator_page()
        elif page_name == "Password History":
            self._render_history_page()
        elif page_name == "Security Guide":
            self._render_security_page()
        elif page_name == "Settings":
            self._render_settings_page()
        else:
            self._render_about_page()

    def _draw_lock_icon(
        self,
        parent: ctk.CTkBaseClass,
        *,
        size: int = 94,
        compact: bool = False,
    ) -> None:
        canvas = tk.Canvas(
            parent,
            width=size,
            height=size,
            bg=parent.cget("fg_color"),
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(expand=True)
        if compact:
            canvas.create_arc(
                14, 11, 32, 31, start=0, extent=180,
                style="arc", outline=COLORS["text"], width=3,
            )
            canvas.create_rectangle(
                12, 21, 34, 37, fill=COLORS["butter"], outline=""
            )
            canvas.create_oval(
                21, 25, 25, 29, fill=COLORS["text"], outline=""
            )
            canvas.create_rectangle(
                22, 28, 24, 33, fill=COLORS["text"], outline=""
            )
            return
        canvas.create_oval(
            7, 7, size - 7, size - 7, fill=COLORS["light_lavender"], outline=""
        )
        canvas.create_oval(
            size * 0.18,
            size * 0.15,
            size * 0.82,
            size * 0.78,
            fill=COLORS["lavender"],
            outline=COLORS["highlight"],
            width=2,
        )
        canvas.create_arc(
            size * 0.34,
            size * 0.23,
            size * 0.66,
            size * 0.62,
            start=0,
            extent=180,
            style="arc",
            outline=COLORS["text"],
            width=max(3, size // 22),
        )
        canvas.create_rectangle(
            size * 0.29,
            size * 0.46,
            size * 0.71,
            size * 0.77,
            fill=COLORS["butter"],
            outline=COLORS["highlight"],
            width=2,
        )
        canvas.create_oval(
            size * 0.47,
            size * 0.54,
            size * 0.53,
            size * 0.61,
            fill=COLORS["text"],
            outline="",
        )
        canvas.create_rectangle(
            size * 0.485,
            size * 0.59,
            size * 0.515,
            size * 0.67,
            fill=COLORS["text"],
            outline="",
        )
        canvas.create_oval(
            size * 0.20,
            size * 0.69,
            size * 0.31,
            size * 0.80,
            fill=COLORS["peach"],
            outline=COLORS["highlight"],
            width=2,
        )
        canvas.create_oval(
            size * 0.70,
            size * 0.18,
            size * 0.79,
            size * 0.27,
            fill=COLORS["mint"],
            outline=COLORS["highlight"],
            width=2,
        )

    def _render_generator_page(self) -> None:
        hero_height = 230
        hero_wrapper, hero = self._clay_card(
            self.page,
            "Your Password Studio",
            "Create strong, unique and secure passwords in seconds.",
            height=hero_height,
            color=COLORS["light_lavender"],
            shadow=COLORS["lavender"],
            radius=25,
        )
        hero_wrapper.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 15))
        hero.grid_columnconfigure(0, weight=1)
        hero.grid_columnconfigure(1, weight=0)

        self.password_entry = ctk.CTkEntry(
            hero,
            textvariable=self.current_password,
            height=48,
            corner_radius=15,
            border_width=1,
            border_color=COLORS["highlight"],
            fg_color=COLORS["card"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
            show="" if self.password_visible.get() else "•",
            state="readonly",
        )
        self.password_entry.grid(row=0, column=0, sticky="ew", padx=(0, 9), pady=(2, 8))
        visibility = self._clay_button(
            hero,
            "Hide" if self.password_visible.get() else "Show",
            self._toggle_password_visibility,
            tone="white",
            width=62,
            height=39,
        )
        visibility.grid(row=0, column=1, sticky="e", pady=(2, 8))
        self.visibility_button = visibility

        action_row = ctk.CTkFrame(hero, fg_color="transparent")
        action_row.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.generate_button = self._clay_button(
            action_row,
            "✳  Generate password",
            self._generate,
            tone="coral",
            width=190,
            height=41,
        )
        self.generate_button.pack(side="left", padx=(0, 8))
        self._clay_button(
            action_row,
            "Copy password",
            self._copy_current,
            tone="lavender",
            width=126,
            height=41,
        ).pack(side="left")
        illustration = ctk.CTkFrame(
            hero,
            width=108,
            height=108,
            corner_radius=26,
            fg_color=COLORS["lavender"],
            border_width=1,
            border_color=COLORS["highlight"],
        )
        illustration.grid(row=0, column=2, rowspan=3, padx=(14, 4), pady=2)
        illustration.grid_propagate(False)
        self._draw_lock_icon(illustration, size=92)

        self._render_category_cards(row=1)
        self._render_options_and_strength(row=3)
        self._render_recent_generated(row=4)

    def _render_category_cards(self, *, row: int) -> None:
        for column, (category, label) in enumerate(CATEGORY_LABELS.items()):
            icon, color, hint = CATEGORY_STYLES[category]
            wrapper, body = self._clay_card(
                self.page,
                label,
                height=121,
                color=color,
                shadow=COLORS["shadow"],
                radius=19,
                heading_color=COLORS["text"],
            )
            wrapper.grid(
                row=row + column // 2,
                column=(column % 2) * 2,
                columnspan=2,
                sticky="nsew",
                padx=(0, 7) if column % 2 == 0 else (7, 0),
                pady=(0, 14),
            )
            body.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                body,
                text=icon,
                font=ctk.CTkFont(family="Consolas", size=17, weight="bold"),
                text_color=COLORS["text"],
                fg_color=COLORS["card"],
                corner_radius=11,
                width=39,
                height=35,
            ).grid(row=0, column=0, sticky="w", padx=(0, 8))
            ctk.CTkLabel(
                body,
                text=hint,
                font=ctk.CTkFont(size=8),
                text_color=COLORS["text"],
                wraplength=100,
                justify="left",
            ).grid(row=0, column=1, sticky="w", padx=(0, 4))
            ctk.CTkCheckBox(
                body,
                text="Include",
                variable=self.category_vars[category],
                checkbox_width=16,
                checkbox_height=16,
                corner_radius=6,
                border_width=2,
                border_color=COLORS["highlight"],
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=9, weight="bold"),
                command=self._update_selection_warning,
            ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(7, 0))

    def _render_options_and_strength(self, *, row: int) -> None:
        length_wrapper, length_card = self._clay_card(
            self.page,
            "Password length",
            "Longer is lovely. Choose from 8 to 128 characters.",
            height=153,
            color=COLORS["card"],
            radius=21,
        )
        length_wrapper.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=(0, 8),
            pady=(0, 15),
        )
        length_card.grid_columnconfigure(0, weight=1)
        self.length_label = ctk.CTkLabel(
            length_card,
            text=f"{self.length.get()} characters",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text"],
            fg_color=COLORS["butter"],
            corner_radius=10,
            padx=10,
            pady=5,
        )
        self.length_label.grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.length_slider = ctk.CTkSlider(
            length_card,
            from_=MIN_PASSWORD_LENGTH,
            to=MAX_PASSWORD_LENGTH,
            number_of_steps=MAX_PASSWORD_LENGTH - MIN_PASSWORD_LENGTH,
            variable=self.length,
            progress_color=COLORS["primary"],
            button_color=COLORS["lavender"],
            button_hover_color=COLORS["primary"],
            fg_color=COLORS["light_lavender"],
            command=self._on_length_change,
        )
        self.length_slider.grid(row=1, column=0, sticky="ew", pady=(0, 7))
        self.exclude_checkbox = ctk.CTkCheckBox(
            length_card,
            text="Exclude look-alike characters (0, O, 1, l, I)",
            variable=self.exclude_ambiguous,
            checkbox_width=15,
            checkbox_height=15,
            corner_radius=6,
            border_width=2,
            border_color=COLORS["shadow"],
            fg_color=COLORS["lavender"],
            hover_color=COLORS["light_lavender"],
            text_color=COLORS["secondary_text"],
            font=ctk.CTkFont(size=9),
        )
        self.exclude_checkbox.grid(row=2, column=0, sticky="w")
        self.selection_warning = ctk.CTkLabel(
            length_card,
            text="",
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color=COLORS["danger"],
            anchor="w",
        )
        self.selection_warning.grid(row=3, column=0, sticky="w", pady=(3, 0))

        strength_wrapper, strength = self._clay_card(
            self.page,
            "Strength check",
            "An educational estimate, not a formal security assessment.",
            height=143,
            color=COLORS["mint"],
            shadow=COLORS["sidebar_shadow"],
            radius=21,
        )
        strength_wrapper.grid(
            row=row,
            column=2,
            columnspan=2,
            sticky="nsew",
            padx=(8, 0),
            pady=(0, 15),
        )
        strength.grid_columnconfigure(0, weight=1)
        self.strength_label = ctk.CTkLabel(
            strength,
            text="READY",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=COLORS["text"],
            fg_color=COLORS["card"],
            corner_radius=10,
            padx=10,
            pady=5,
        )
        self.strength_label.grid(row=0, column=0, sticky="w", pady=(0, 7))
        self.strength_bar = ctk.CTkProgressBar(
            strength,
            height=9,
            corner_radius=6,
            progress_color=COLORS["primary"],
            fg_color=COLORS["sidebar"],
        )
        self.strength_bar.grid(row=1, column=0, sticky="ew", pady=(0, 7))
        self.strength_bar.set(0)
        self.strength_message = ctk.CTkLabel(
            strength,
            text="Generate a password to see a strength note.",
            font=ctk.CTkFont(size=9),
            text_color=COLORS["text"],
            wraplength=420,
            justify="left",
        )
        self.strength_message.grid(row=2, column=0, sticky="w")
        if self.current_password.get():
            self._update_strength(evaluate_strength(self.current_password.get()))
        self._update_selection_warning()

    def _render_recent_generated(self, *, row: int) -> None:
        entries = self.history.entries
        height = 99 + max(1, len(entries)) * 42 + (34 if entries else 0)
        recent_wrapper, recent = self._clay_card(
            self.page,
            "Recently Generated",
            "Only the last five passwords are held in memory for this session.",
            height=height,
            color=COLORS["card"],
            radius=21,
        )
        recent_wrapper.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(0, 15))
        if not entries:
            ctk.CTkLabel(
                recent,
                text="Your new passwords will appear here.",
                font=ctk.CTkFont(size=9),
                text_color=COLORS["muted"],
            ).pack(anchor="w", pady=(3, 0))
            return
        toolbar = ctk.CTkFrame(recent, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 3))
        ctk.CTkFrame(toolbar, fg_color="transparent").pack(side="left", expand=True)
        self._clay_button(
            toolbar,
            "Clear history",
            self._clear_history,
            tone="white",
            width=101,
            height=27,
        ).pack(side="right")
        for entry in entries:
            self._history_row(recent, entry, compact=True)

    def _history_row(
        self,
        parent: ctk.CTkBaseClass,
        entry: HistoryEntry,
        *,
        compact: bool = False,
    ) -> None:
        row_color = COLORS["card"]
        row = ctk.CTkFrame(
            parent,
            fg_color=row_color,
            corner_radius=13,
            border_width=1,
            border_color=COLORS["border"],
        )
        row.pack(fill="x", pady=(3 if compact else 6, 0))
        row.grid_columnconfigure(0, weight=1)

        shown = self._history_visibility.get(id(entry), False)
        field = ctk.CTkEntry(
            row,
            height=30,
            fg_color="transparent",
            border_width=0,
            text_color=COLORS["text"],
            font=ctk.CTkFont(family="Consolas", size=10),
            show="" if shown else "•",
            state="normal",
        )
        field.insert(0, entry.password)
        field.configure(state="readonly")
        field.grid(row=0, column=0, sticky="ew", padx=(9, 5), pady=(3, 0))
        ctk.CTkLabel(
            row,
            text=entry.generated_at.strftime("%b %d, %I:%M %p"),
            font=ctk.CTkFont(size=8),
            text_color=COLORS["secondary_text"],
        ).grid(row=1, column=0, sticky="w", padx=11, pady=(0, 4))

        controls = ctk.CTkFrame(row, fg_color="transparent")
        controls.grid(row=0, column=1, rowspan=2, padx=5)
        self._clay_button(
            controls,
            "Hide" if shown else "Show",
            lambda current=entry, current_field=field: self._toggle_history_entry(
                current, current_field
            ),
            tone="lavender",
            width=45,
            height=25,
        ).pack(side="left", padx=2)
        self._clay_button(
            controls,
            "Copy",
            lambda password=entry.password: self._copy_value(password),
            tone="white",
            width=42,
            height=25,
        ).pack(side="left", padx=2)

    def _render_history_page(self) -> None:
        entries = self.history.entries
        wrapper, body = self._clay_card(
            self.page,
            "Recently Generated",
            "The five latest passwords. Nothing here is saved after you close the app.",
            height=132 + max(1, len(entries)) * 44 + (42 if entries else 0),
            color=COLORS["light_lavender"],
            shadow=COLORS["lavender"],
            radius=23,
        )
        wrapper.grid(row=0, column=0, columnspan=4, sticky="ew")
        if not entries:
            ctk.CTkLabel(
                body,
                text="Nothing here yet. Generate a password and it will appear here.",
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text"],
            ).pack(anchor="w", pady=(7, 0))
            return
        toolbar = ctk.CTkFrame(body, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 3))
        ctk.CTkFrame(toolbar, fg_color="transparent").pack(side="left", expand=True)
        self._clay_button(
            toolbar,
            "Clear history",
            self._clear_history,
            tone="white",
            width=104,
            height=29,
        ).pack(side="right")
        for entry in entries:
            self._history_row(body, entry)

    def _render_settings_page(self) -> None:
        wrapper, settings = self._clay_card(
            self.page,
            "Password preferences",
            "These choices are applied whenever you make a new password.",
            height=172,
            color=COLORS["butter"],
            shadow=COLORS["butter"],
            radius=22,
        )
        wrapper.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 13))
        settings.grid_columnconfigure(0, weight=1)
        self.length_label = ctk.CTkLabel(
            settings,
            text=f"{self.length.get()} characters",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text"],
            fg_color=COLORS["card"],
            corner_radius=10,
            padx=10,
            pady=5,
        )
        self.length_label.pack(anchor="w", pady=(2, 5))
        self.length_slider = ctk.CTkSlider(
            settings,
            from_=MIN_PASSWORD_LENGTH,
            to=MAX_PASSWORD_LENGTH,
            number_of_steps=MAX_PASSWORD_LENGTH - MIN_PASSWORD_LENGTH,
            variable=self.length,
            progress_color=COLORS["primary"],
            button_color=COLORS["lavender"],
            button_hover_color=COLORS["primary"],
            fg_color=COLORS["card"],
            command=self._on_length_change,
        )
        self.length_slider.pack(fill="x", pady=(0, 7))
        self.exclude_checkbox = ctk.CTkCheckBox(
            settings,
            text="Exclude ambiguous characters (0, O, 1, l, I)",
            variable=self.exclude_ambiguous,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=6,
            border_width=2,
            border_color=COLORS["shadow"],
            fg_color=COLORS["lavender"],
            hover_color=COLORS["light_lavender"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=9),
        )
        self.exclude_checkbox.pack(anchor="w")

        self._render_category_cards(row=1)
        self._render_selection_warning(row=3)

    def _render_selection_warning(self, *, row: int) -> None:
        wrapper, warning = self._clay_card(
            self.page,
            "A note about character groups",
            "At least two groups need to be selected before you can generate a password.",
            height=105,
            color=COLORS["peach"],
            shadow=COLORS["peach"],
            radius=20,
        )
        wrapper.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(12, 0))
        self.selection_warning = ctk.CTkLabel(
            warning,
            text="",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text"],
        )
        self.selection_warning.pack(anchor="w")
        self._update_selection_warning()

    def _render_security_page(self) -> None:
        tips = (
            ("01", "Long is lovely", "A longer password gives guessing attempts more possibilities to work through.", COLORS["light_lavender"]),
            ("02", "One account, one password", "Unique passwords keep one exposed account from putting your other accounts at risk.", COLORS["mint"]),
            ("03", "A little variety helps", "Use a mix of letters, numbers, and symbols to add variety to your password.", COLORS["sky"]),
            ("04", "Keep your password yours", "Avoid sharing passwords through email, messages, or a shared screen.", COLORS["peach"]),
            ("05", "Let a password manager help", "A trusted password manager can create and remember unique credentials for you.", COLORS["butter"]),
            ("06", "Turn on another layer", "Multi-factor authentication adds another check to help protect your accounts.", COLORS["lavender"]),
        )
        for index, (number, title, description, color) in enumerate(tips):
            wrapper, body = self._clay_card(
                self.page,
                f"{number}   {title}",
                description,
                height=137,
                color=color,
                radius=20,
                description_width=320,
            )
            wrapper.grid(
                row=index // 2,
                column=(index % 2) * 2,
                columnspan=2,
                sticky="nsew",
                padx=(0, 7) if index % 2 == 0 else (7, 0),
                pady=(0, 13),
            )
            ctk.CTkLabel(
                body,
                text="A small habit makes a lovely difference.",
                font=ctk.CTkFont(size=8, weight="bold"),
                text_color=COLORS["text"],
            ).pack(anchor="w", pady=(3, 0))

    def _render_about_page(self) -> None:
        wrapper, body = self._clay_card(
            self.page,
            "Securely.  A little workshop for safer passwords.",
            "A friendly local desktop application designed with privacy in mind.",
            height=240,
            color=COLORS["light_lavender"],
            shadow=COLORS["lavender"],
            radius=23,
        )
        wrapper.grid(row=0, column=0, columnspan=4, sticky="ew")
        for detail in (
            f"Version {APP_VERSION}",
            "Built with Python, CustomTkinter, pyperclip, and the standard-library secrets module.",
            "Passwords are generated locally; history remains in memory for this session only.",
            "The strength indicator is an educational estimate, not a formal security assessment.",
        ):
            ctk.CTkLabel(
                body,
                text=f"•  {detail}",
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text"],
                wraplength=700,
                justify="left",
            ).pack(anchor="w", pady=(4, 5))

    def _on_length_change(self, value: float) -> None:
        selected_length = round(value)
        self.length.set(selected_length)
        if hasattr(self, "length_label") and self.length_label.winfo_exists():
            self.length_label.configure(text=f"{selected_length} characters")

    def _update_selection_warning(self) -> None:
        if not hasattr(self, "selection_warning"):
            return
        try:
            if not self.selection_warning.winfo_exists():
                return
        except tk.TclError:
            return
        selected_count = sum(variable.get() for variable in self.category_vars.values())
        self.selection_warning.configure(
            text=(
                "Choose at least two character groups."
                if selected_count < 2
                else ""
            )
        )

    def _generate(self) -> None:
        selected = [
            category
            for category, variable in self.category_vars.items()
            if variable.get()
        ]
        try:
            password = generate_password(
                self.length.get(), selected, self.exclude_ambiguous.get()
            )
        except ValueError as error:
            LOGGER.info("Password generation validation failed: %s", error)
            self._show_notification(str(error), COLORS["danger"])
            return
        except Exception:
            LOGGER.exception("Unexpected password generation error.")
            self._show_notification(
                "Something went wrong while making your password.", COLORS["danger"]
            )
            return

        self.current_password.set(password)
        self.password_visible.set(True)
        self.history.add(password)
        self._history_visibility = {
            id(entry): self._history_visibility.get(id(entry), False)
            for entry in self.history.entries
        }
        strength = evaluate_strength(password)
        if self._active_page != "Password Generator":
            self._show_page("Password Generator")
        else:
            self._show_page(self._active_page)
        self._update_strength(strength)

        try:
            copy_to_clipboard(password)
        except ClipboardError as error:
            LOGGER.warning("Could not copy generated password: %s", error)
            self._show_notification(
                "Password made, but clipboard access failed.", COLORS["warning"]
            )
            return
        self._show_notification("Password generated and copied.", COLORS["success"])

    def _update_strength(self, result: StrengthResult) -> None:
        color = STRENGTH_COLORS.get(result.label, COLORS["muted"])
        self.strength_label.configure(text=result.label, fg_color=color)
        self.strength_bar.configure(progress_color=color)
        self.strength_bar.set(result.score / 100)
        self.strength_message.configure(text=result.message)

    def _toggle_password_visibility(self) -> None:
        visible = not self.password_visible.get()
        self.password_visible.set(visible)
        self.password_entry.configure(show="" if visible else "•")
        self.visibility_button.configure(text="Hide" if visible else "Show")

    def _toggle_history_entry(
        self, entry: HistoryEntry, field: ctk.CTkEntry
    ) -> None:
        visible = not self._history_visibility.get(id(entry), False)
        self._history_visibility[id(entry)] = visible
        field.configure(show="" if visible else "•")
        for child in field.master.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                for button in child.winfo_children():
                    if isinstance(button, ctk.CTkButton) and button.cget("text") in (
                        "Show",
                        "Hide",
                    ):
                        button.configure(text="Hide" if visible else "Show")

    def _copy_current(self) -> None:
        password = self.current_password.get()
        if not password:
            self._show_notification(
                "Generate a password before copying it.", COLORS["warning"]
            )
            return
        self._copy_value(password)

    def _copy_value(self, password: str) -> None:
        try:
            copy_to_clipboard(password)
        except ClipboardError as error:
            LOGGER.warning("Clipboard copy failed: %s", error)
            self._show_notification(
                "Clipboard unavailable. Check your desktop clipboard support.",
                COLORS["warning"],
            )
            return
        self._show_notification("Copied to clipboard.", COLORS["success"])

    def _show_notification(self, message: str, color: str) -> None:
        if hasattr(self, "notification"):
            try:
                if self.notification.winfo_exists():
                    self.notification.configure(text=message, text_color=color)
            except tk.TclError:
                LOGGER.debug("Notification is not visible on the current page.")

    def _clear_history(self) -> None:
        self.history.clear()
        self._history_visibility.clear()
        if self._active_page == "Password History":
            self._show_page("Password History")
        else:
            self._show_page("Password Generator")
        self._show_notification("Session history cleared.", COLORS["success"])

    def _report_callback_exception(
        self,
        exception_type: type[BaseException],
        error: BaseException,
        traceback: TracebackType | None,
    ) -> None:
        LOGGER.error(
            "Unexpected application error.",
            exc_info=(exception_type, error, traceback),
        )
        messagebox.showerror(
            "Application error",
            "Something unexpected happened. Please restart the application.",
            parent=self.root,
        )

    def _on_close(self) -> None:
        self.history.clear()
        self._history_visibility.clear()
        self.current_password.set("")
        self.root.destroy()
