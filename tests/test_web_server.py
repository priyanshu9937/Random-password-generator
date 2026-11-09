import unittest

from app.generator import AMBIGUOUS_CHARACTERS
from app.history import PasswordHistory
from app.web_server import create_app


class LocalWebsiteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.history = PasswordHistory()
        self.app = create_app(self.history)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_homepage_and_assets_are_served(self) -> None:
        with self.client.get("/") as page:
            self.assertEqual(page.status_code, 200)
            self.assertIn(b"Your Password", page.data)
            self.assertIn(b'data-route="settings"', page.data)
            self.assertIn(b'data-view="settings"', page.data)
            self.assertIn("default-src 'self'", page.headers["Content-Security-Policy"])
            self.assertEqual(page.headers["X-Content-Type-Options"], "nosniff")
        with self.client.get("/assets/styles.css") as styles:
            self.assertEqual(styles.status_code, 200)
        with self.client.get("/assets/app.js") as script:
            self.assertEqual(script.status_code, 200)
        with self.client.get("/assets/favicon.svg") as favicon:
            self.assertEqual(favicon.status_code, 200)
            self.assertEqual(favicon.mimetype, "image/svg+xml")

    def test_health_endpoint(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_generate_password_returns_strength_and_adds_session_history(self) -> None:
        response = self.client.post(
            "/api/generate",
            json={
                "length": 32,
                "categories": ["uppercase", "lowercase", "numbers", "symbols"],
            },
        )
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data["password"]), 32)
        self.assertTrue(any(char.isupper() for char in data["password"]))
        self.assertTrue(any(char.islower() for char in data["password"]))
        self.assertTrue(any(char.isdigit() for char in data["password"]))
        self.assertTrue(any(not char.isalnum() for char in data["password"]))
        self.assertIn(data["strength"]["label"], {"WEAK", "MEDIUM", "STRONG"})
        self.assertIn("message", data["strength"])
        self.assertEqual(len(self.history.entries), 1)

    def test_generation_can_exclude_ambiguous_characters(self) -> None:
        response = self.client.post(
            "/api/generate",
            json={
                "length": 128,
                "categories": ["uppercase", "lowercase", "numbers", "symbols"],
                "exclude_ambiguous": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        password = response.get_json()["password"]
        self.assertEqual(len(password), 128)
        self.assertTrue(AMBIGUOUS_CHARACTERS.isdisjoint(password))

    def test_generation_rejects_invalid_lengths_and_categories(self) -> None:
        invalid_payloads = (
            {"length": 7, "categories": ["uppercase", "lowercase"]},
            {"length": 129, "categories": ["uppercase", "lowercase"]},
            {"length": True, "categories": ["uppercase", "lowercase"]},
            {"length": 16, "categories": ["uppercase"]},
            {"length": 16, "categories": ["uppercase", "invalid"]},
            {"length": 16, "categories": "uppercase"},
            {
                "length": 16,
                "categories": ["uppercase", "lowercase"],
                "exclude_ambiguous": "yes",
            },
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/api/generate", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())
        self.assertEqual(self.history.entries, ())

    def test_generation_rejects_non_json_request(self) -> None:
        response = self.client.post("/api/generate", data="password=secret")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_history_is_limited_to_five_recent_passwords(self) -> None:
        passwords = []
        for _ in range(6):
            response = self.client.post(
                "/api/generate",
                json={"length": 16, "categories": ["uppercase", "lowercase"]},
            )
            self.assertEqual(response.status_code, 200)
            passwords.append(response.get_json()["password"])

        data = self.client.get("/api/history").get_json()
        self.assertEqual(data["limit"], 5)
        self.assertEqual(len(data["entries"]), 5)
        self.assertEqual(data["entries"][0]["password"], passwords[-1])
        self.assertEqual([entry.password for entry in self.history.entries], passwords[-1:-6:-1])

    def test_history_can_be_cleared(self) -> None:
        self.history.add("session-only-test")
        response = self.client.delete("/api/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"cleared": True})
        self.assertEqual(self.client.get("/api/history").get_json()["entries"], [])

    def test_unknown_api_route_returns_json_error(self) -> None:
        response = self.client.get("/api/missing")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
