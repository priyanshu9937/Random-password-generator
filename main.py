"""Start the local Securely password-generator website."""

import logging

from app.web_server import main as run_website


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    run_website()


if __name__ == "__main__":
    main()
