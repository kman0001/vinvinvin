import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.source import (
    SourceError,
    build_constants_url,
    get_constants_url,
    parse_apps_script_url,
    parse_menu,
    read_apps_script_url,
)


CONSTANTS_SOURCE = """export const API =
    "https://script.google.com/macros/s/example/exec";
"""


class ParseMenuTests(unittest.TestCase):

    def test_parses_api_export_from_constants_source(self):
        self.assertEqual(
            parse_apps_script_url(CONSTANTS_SOURCE),
            "https://script.google.com/macros/s/example/exec"
        )

    def test_reads_api_export_from_website_constants_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            constants = Path(temp_dir) / "constants.js"
            constants.write_text(CONSTANTS_SOURCE, encoding="utf-8")

            self.assertEqual(
                read_apps_script_url(constants),
                "https://script.google.com/macros/s/example/exec"
            )

    def test_builds_constants_url_from_base_url(self):
        self.assertEqual(
            build_constants_url("https://vinvinvin-gunja.vercel.app"),
            "https://vinvinvin-gunja.vercel.app/js/config/constants.js"
        )

    def test_builds_constants_url_with_custom_path(self):
        self.assertEqual(
            build_constants_url("https://example.com/app/", "assets/constants.js"),
            "https://example.com/app/assets/constants.js"
        )

    def test_prefers_base_url_config_key(self):
        self.assertEqual(
            get_constants_url({
                "source": {
                    "base_url": "https://example.com",
                    "constants_url": "https://legacy.example.com/constants.js"
                }
            }),
            "https://example.com/js/config/constants.js"
        )

    def test_keeps_constants_url_as_legacy_location(self):
        self.assertEqual(
            get_constants_url({
                "source": {"constants_url": "https://example.com/js/config/constants.js"}
            }),
            "https://example.com/js/config/constants.js"
        )

    def test_parses_apps_script_menu_rows(self):
        items = parse_menu({
            "menu": [
                {"종류": " 레드 ", "이름": " 와인 A ", "사진": " https://example.com/a.webp "},
                {"종류": "안주", "이름": "치즈", "사진": "cheese.webp"},
                {"종류": "화이트", "이름": "사진 없음", "사진": ""},
            ]
        })

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].category, "레드")
        self.assertEqual(items[0].name, "와인 A")
        self.assertTrue(items[0].is_url)
        self.assertFalse(items[0].is_local_webp)
        self.assertEqual(items[1].category, "안주")
        self.assertFalse(items[1].is_url)
        self.assertTrue(items[1].is_local_webp)

    def test_rejects_payload_without_menu_array(self):
        with self.assertRaises(SourceError):
            parse_menu({"items": []})


if __name__ == "__main__":
    unittest.main()
