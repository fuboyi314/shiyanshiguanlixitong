import json
import tempfile
import unittest
from pathlib import Path

from webui.server import DEFAULT_CONFIG, load_ui_config, run_demo_schedule, save_ui_config


class TestWebUIServerConfigIO(unittest.TestCase):
    def test_load_returns_default_when_file_missing(self) -> None:
        path = Path(tempfile.mkdtemp(prefix="webui-test-")) / "missing.json"
        loaded = load_ui_config(path)
        self.assertEqual(loaded["semester"]["semester_name"], DEFAULT_CONFIG["semester"]["semester_name"])
        self.assertIn("lab_tasks", loaded)

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
            "lab_tasks": [],
            "schedule_result": {"scheduled_items": [], "unscheduled_items": []},
        }
        save_ui_config(config, path)

        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(raw["semester"]["total_weeks"], 18)

        loaded = load_ui_config(path)
        self.assertEqual(loaded["semester"]["holidays"][0]["name"], "国庆节")

    def test_run_demo_schedule(self) -> None:
        config = {
            "theory_slots": [{"class_name": "计科231", "course_name": "数据结构", "start_period": 1}],
            "labs": [{"lab_id": "LAB-A", "lab_name": "A实验室", "capacity": 50, "supported_courses": ["数据结构"]}],
            "lab_tasks": [
                {
                    "task_id": "TASK-1",
                    "class_name": "计科231",
                    "course_name": "数据结构",
                    "project_name": "图实验",
                    "student_count": 40,
                    "duration_periods": 2,
                    "expected_week": 6,
                    "expected_weekday": 2,
                    "teacher": "张老师",
                },
                {
                    "task_id": "TASK-2",
                    "class_name": "计科232",
                    "course_name": "数据库",
                    "project_name": "SQL实验",
                    "student_count": 40,
                    "duration_periods": 2,
                    "expected_week": 6,
                    "expected_weekday": 2,
                    "teacher": "李老师",
                },
            ],
        }
        scheduled, unscheduled = run_demo_schedule(config)
        self.assertEqual(len(scheduled), 1)
        self.assertEqual(len(unscheduled), 1)
        self.assertEqual(unscheduled[0].reason, "无课程匹配实验室")


if __name__ == "__main__":
    unittest.main()
