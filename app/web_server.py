"""Loopback-only web interface backed by the existing password modules."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

from app.config import MAX_HISTORY_ITEMS, MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from app.generator import generate_password
from app.history import PasswordHistory
from app.strength import evaluate_strength

WEB_DIRECTORY = Path(__file__).with_name("web")
DEFAULT_CATEGORIES = ["uppercase", "lowercase", "numbers", "symbols"]


def create_app(history: PasswordHistory | None = None) -> Flask:
    """Create the local website and JSON API with process-memory history."""
    app = Flask(__name__, static_folder=None)
    password_history = history if history is not None else PasswordHistory()
    app.config["PASSWORD_HISTORY"] = password_history

    @app.after_request
    def set_security_headers(response: Response) -> Response:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        return send_from_directory(WEB_DIRECTORY, "index.html")

    @app.get("/assets/<path:filename>")
    def assets(filename: str):
        return send_from_directory(WEB_DIRECTORY / "assets", filename)

    @app.get("/api/history")
    def get_history():
        entries = [
            {
                "password": entry.password,
                "generated_at": entry.generated_at.isoformat(timespec="minutes"),
            }
            for entry in password_history.entries
        ]
        return jsonify({"entries": entries, "limit": MAX_HISTORY_ITEMS})

    @app.post("/api/generate")
    def generate():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Send password settings as a JSON object."}), 400

        length = payload.get("length", 16)
        categories = payload.get("categories", DEFAULT_CATEGORIES)
        exclude_ambiguous = payload.get("exclude_ambiguous", False)
        if isinstance(length, bool) or not isinstance(length, int):
            return jsonify({"error": "Password length must be a whole number."}), 400
        if not MIN_PASSWORD_LENGTH <= length <= MAX_PASSWORD_LENGTH:
            return (
                jsonify(
                    {
                        "error": (
                            f"Choose a length from {MIN_PASSWORD_LENGTH} "
                            f"to {MAX_PASSWORD_LENGTH} characters."
                        )
                    }
                ),
                400,
            )
        if not isinstance(categories, list) or not all(
            isinstance(category, str) for category in categories
        ):
            return jsonify({"error": "Choose valid character categories."}), 400
        if not isinstance(exclude_ambiguous, bool):
            return jsonify({"error": "Choose a valid ambiguous-character setting."}), 400

        try:
            password = generate_password(length, categories, exclude_ambiguous)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        entry = password_history.add(password)
        strength = evaluate_strength(password)
        app.logger.info(
            "Generated password (length=%d, category_count=%d).",
            length,
            len(set(categories)),
        )
        return jsonify(
            {
                "password": password,
                "generated_at": entry.generated_at.isoformat(timespec="minutes"),
                "strength": {
                    "label": strength.label,
                    "score": strength.score,
                    "message": strength.message,
                },
            }
        )

    @app.delete("/api/history")
    def clear_history():
        password_history.clear()
        return jsonify({"cleared": True})

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(error: Exception):
        if request.path.startswith("/api/"):
            return jsonify({"error": "That API route was not found."}), 404
        return error

    return app


def main() -> None:
    """Start the website on localhost; do not expose the password API to a LAN."""
    import webbrowser
    from threading import Timer

    app = create_app()
    url = "http://127.0.0.1:8765"
    Timer(0.8, webbrowser.open, args=(url,)).start()
    app.run(host="127.0.0.1", port=8765, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
