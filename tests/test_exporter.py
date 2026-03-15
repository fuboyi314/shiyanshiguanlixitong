import importlib.util
import tempfile
import unittest
from pathlib import Path

from data_models.models import ScheduledItem, UnscheduledItem

PANDAS_AVAILABLE = importlib.util.find_spec("pandas") is not None


@unittest.skipUnless(PANDAS_AVAILABLE, "pandas is required for exporter tests")
class TestExporter(unittest.TestCase):
    def test_export_schedule_result(self) -> None:
        import pandas as pd

        from services.exporter import export_schedule_result

        scheduled_items = [
            ScheduledItem(
                task_id="TASK-001",
                class_name="计科231",
                course_name="数据结构",
                project_name="图算法综合实验",
                lab_id="LAB-A101",
                lab_name="计算机基础实验室",
                week=6,
                weekday=2,
                start_period=3,
                end_period=4,
                teacher="张老师",
            ),
            ScheduledItem(
                task_id="TASK-002",
                class_name="计科231",
                course_name="数据结构",
                project_name="树结构实验",
                lab_id="LAB-A101",
                lab_name="计算机基础实验室",
                week=7,
                weekday=2,
                start_period=5,
                end_period=6,
                teacher="张老师",
            ),
        ]
        unscheduled_items = [
            UnscheduledItem(
                task_id="TASK-003",
                class_name="计科232",
                course_name="数据库原理",
                project_name="SQL优化实验",
                reason="无可用实验室",
                teacher="李老师",
            )
        ]

        out_dir = Path(tempfile.mkdtemp(prefix="exporter-test-"))
        out_file = out_dir / "result.xlsx"

        export_schedule_result(str(out_file), scheduled_items, unscheduled_items)

        self.assertTrue(out_file.exists())
        xl = pd.ExcelFile(out_file)
        self.assertEqual(set(xl.sheet_names), {"已排课", "未排课", "实验室利用率", "班级统计"})


if __name__ == "__main__":
    unittest.main()
