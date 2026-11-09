# Securely — Secure Password Generator

Securely is a locally hosted, responsive website for creating unique, cryptographically secure passwords. It combines a considered, editorial interface with a Python backend that generates passwords using the standard-library `secrets` module. Passwords are processed locally; nothing is sent to a third-party service.

The project also retains its CustomTkinter desktop interface in `app/gui.py`. `main.py` starts the website by default.

## Features

- Generate 8–128 character passwords with uppercase, lowercase, numbers, and symbols.
- Guarantee a character from every selected category, then securely shuffle the result.
- Exclude ambiguous characters (`0`, `O`, `1`, `l`, and `I`).
- Copy a new password automatically when browser clipboard permissions allow, or copy it on request.
- Reveal or mask generated passwords and individual history entries.
- Display a clearly labeled educational strength estimate.
- Keep up to five generated passwords in server-process memory only; clear history any time.
- Responsive Dashboard, Generator, History, Security Guide, and About views.
- Serve the website and its API on `127.0.0.1` only.

## Interface

The website uses a warm-white foundation with mint navigation, a lavender password studio, coral calls to action, and restrained pastel configuration accents. Custom SVG icons and a small CSS lock illustration are included locally. Mobile navigation, reduced-motion preferences, keyboard generation (`Enter`), focus states, and clear success/error feedback are supported.

## Technology

- Python 3.12+
- Flask for the loopback website and JSON API
- Existing Python `secrets`, strength, and session-history modules
- HTML, responsive CSS, and vanilla JavaScript
- CustomTkinter remains available for the desktop UI
- `unittest` for automated tests

No frontend build step or external fonts, icon services, or JavaScript packages are required.

## Architecture

```text
main.py                    Local website entry point
app/
  config.py                Shared application settings
  generator.py             Validated, secure password generation
  strength.py              Educational strength estimate
  history.py               Bounded in-memory history
  utils.py                 Clipboard helper for desktop UI
  gui.py                   Retained CustomTkinter desktop interface
  web_server.py            Loopback Flask app and API endpoints
  web/
    index.html             Website views and accessible controls
    assets/
      app.js               Navigation, API, clipboard, and interactions
      styles.css           Design system and responsive breakpoints
tests/
  test_generator.py
  test_strength.py
  test_history.py
  test_web_server.py
requirements.txt
```

The web API delegates generation, strength evaluation, and history to the existing Python modules. Passwords are not written to logs, files, or databases. The server binds to loopback rather than exposing the password API to the local network.

## Installation

From the project directory, create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you already created `.venv`, activate it before installing dependencies. On systems without the Windows `py` launcher, use `python3 -m venv .venv`.

## Run the website

```powershell
python main.py
```

Securely opens `http://127.0.0.1:8765` in your browser. The app is designed for local use; keep the server bound to localhost.

## Run the retained desktop interface

```powershell
python -c "import customtkinter as ctk; from app.gui import PasswordGeneratorApp; root=ctk.CTk(); PasswordGeneratorApp(root); root.mainloop()"
```

## Tests

```powershell
python -m unittest discover -v
```

## Security notes

Python's `secrets` module is intended for security-sensitive randomness. Every selected category is represented before the resulting password is shuffled. The strength indicator is an educational heuristic, not a mathematical entropy calculation, formal assessment, or guarantee. Browser clipboard access requires browser permission; if unavailable, the password remains visible for manual copying. The latest five passwords exist only in the local server process's memory and are cleared when it exits. Use unique passwords and consider storing them in a trusted password manager.
