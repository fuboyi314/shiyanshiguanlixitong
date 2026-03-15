import json
import tempfile
import unittest
from pathlib import Path

from webui.server import DEFAULT_CONFIG, load_ui_config, save_ui_config


class TestWebUIServerConfigIO(unittest.TestCase):
    def test_load_returns_default_when_file_missing(self) -> None:
        path = Path(tempfile.mkdtemp(prefix="webui-test-")) / "missing.json"
        loaded = load_ui_config(path)
        self.assertEqual(loaded["semester"]["semester_name"], DEFAULT_CONFIG["semester"]["semester_name"])

    def test_save_then_load_roundtrip(self) -> None:
        path = Path(tempfile.mkdtemp(prefix="webui-test-")) / "config.json"
        config = {
            "semester": {
                "semester_name": "2026-2027-1",
                "start_date": "2026-09-01",
                "total_weeks": 18,
                "periods_per_day": 10,
                "working_days": [1, 2, 3, 4, 5],
                "holidays": [{"date": "2026-10-01", "name": "国庆节"}],
            },
            "theory_slots": [],
            "labs": [],
        }
        save_ui_config(config, path)

        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(raw["semester"]["total_weeks"], 18)

        loaded = load_ui_config(path)
        self.assertEqual(loaded["semester"]["holidays"][0]["name"], "国庆节")


if __name__ == "__main__":
    unittest.main()
