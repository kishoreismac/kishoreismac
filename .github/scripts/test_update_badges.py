import io
import json
import unittest
from unittest.mock import patch

import update_badges as updater


def badge(identifier="one", date="2023-04-08"):
    return {"id": identifier, "public": True, "state": "accepted",
            "issued_at_date": date, "image_url": "https://images.credly.com/images/test.png",
            "badge_template": {"name": 'Azure & "Cloud"'}}


class BadgeTests(unittest.TestCase):
    def test_profile_inputs(self):
        for profile in ("kiran-kumar-nune", "https://www.credly.com/users/kiran-kumar-nune/badges",
                        "https://www.credly.com/users/kiran-kumar-nune/edit/badges/credly"):
            self.assertEqual(updater.profile_username(profile), "kiran-kumar-nune")
        for profile in ("", "nunekiran@outlook.com", "https://example.com/users/person"):
            with self.assertRaises(ValueError):
                updater.profile_username(profile)

    def test_pagination_sorting_and_private_badges(self):
        private = dict(badge("private"), public=False)
        pages = [{"data": [badge(), private], "metadata": {"total_pages": 2}},
                 {"data": [badge("new", "2025-01-01"), badge()], "metadata": {"total_pages": 2}}]
        with patch.object(updater, "urlopen", side_effect=[io.BytesIO(json.dumps(p).encode()) for p in pages]) as fetch:
            self.assertEqual([b["id"] for b in updater.fetch_badges("person")], ["new", "one"])
            self.assertIn("page=2", fetch.call_args.args[0].full_url)

    def test_empty_response_fails(self):
        with patch.object(updater, "urlopen", return_value=io.BytesIO(b'{"data": [], "metadata": {"total_pages": 0}}')):
            with self.assertRaisesRegex(ValueError, "No public"):
                updater.fetch_badges("person")

    def test_readme_preservation_and_repeat_run(self):
        source = "Hi 👋\r\n" + updater.START + "\nold\n" + updater.END + "\r\nOther content"
        result = updater.update_readme(source, [badge()])
        self.assertTrue(result.startswith("Hi 👋\r\n"))
        self.assertTrue(result.endswith("\r\nOther content"))
        self.assertIn('Azure &amp; &quot;Cloud&quot;', result)
        self.assertIn("/badges/one/public_url", result)
        self.assertEqual(updater.update_readme(result, [badge()]), result)

    def test_bad_markers_fail(self):
        for source in ("no markers", updater.END + updater.START, updater.START * 2 + updater.END):
            with self.assertRaises(ValueError):
                updater.update_readme(source, [badge()])

    def test_limit(self):
        self.assertEqual(updater.render_badges([badge(str(i)) for i in range(12)]).count("<img "), 10)


if __name__ == "__main__":
    unittest.main()
