import importlib.util
import tempfile
import unittest
from pathlib import Path

from utils.config import get_default_field_mappings

PANDAS_AVAILABLE = importlib.util.find_spec("pandas") is not None


@unittest.skipUnless(PANDAS_AVAILABLE, "pandas is required for excel loader tests")
class TestExcelLoader(unittest.TestCase):
    def setUp(self) -> None:
        import pandas as pd
        from services.excel_loader import (
            ExcelLoadError,
            load_lab_tasks,
            load_labs,
            load_theory_class_slots,
        )

        self.pd = pd
        self.ExcelLoadError = ExcelLoadError
        self.load_theory_class_slots = load_theory_class_slots
        self.load_labs = load_labs
        self.load_lab_tasks = load_lab_tasks
        self.mappings = get_default_field_mappings()

    def _save_df(self, df, name: str) -> str:
        tmp_dir = Path(tempfile.mkdtemp(prefix="excel-loader-test-"))
        file_path = tmp_dir / name
        df.to_excel(file_path, index=False)
        return str(file_path)

    def test_load_theory_slots(self) -> None:
        df = self.pd.DataFrame(
            [
                {
                    "班级": "计科231",
                    "课程": "数据结构",
                    "教师": "张老师",
                    "星期": 1,
                    "开始节次": 1,
                    "结束节次": 2,
                    "周次": "1-3,5",
                    "学期": "2025-2026-1",
                }
            ]
        )
        path = self._save_df(df, "theory.xlsx")
        rows = self.load_theory_class_slots(path, self.mappings["theory"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].weeks, [1, 2, 3, 5])

    def test_load_labs(self) -> None:
        df = self.pd.DataFrame(
            [
                {
                    "实验室编号": "LAB-A101",
                    "实验室名称": "计算机基础实验室",
                    "容量": 50,
                    "校区": "主校区",
                    "可用课程": "数据结构,数据库原理",
                }
            ]
        )
        path = self._save_df(df, "labs.xlsx")
        rows = self.load_labs(path, self.mappings["lab"])
        self.assertEqual(rows[0].supported_courses, ["数据结构", "数据库原理"])

    def test_load_tasks_and_type_error(self) -> None:
        ok_df = self.pd.DataFrame(
            [
                {
                    "任务编号": "TASK-001",
                    "班级": "计科231",
                    "课程": "数据结构",
                    "实验项目": "图算法综合实验",
                    "人数": 46,
                    "时长节次": 2,
                    "期望周": 6,
                    "期望星期": 2,
                    "教师": "张老师",
                    "备注": "需要投影",
                }
            ]
        )
        ok_path = self._save_df(ok_df, "task-ok.xlsx")
        rows = self.load_lab_tasks(ok_path, self.mappings["task"])
        self.assertEqual(rows[0].expected_week, 6)

        bad_df = ok_df.copy()
        bad_df.loc[0, "人数"] = "约40人"
        bad_path = self._save_df(bad_df, "task-bad.xlsx")
        with self.assertRaises(self.ExcelLoadError):
            self.load_lab_tasks(bad_path, self.mappings["task"])


if __name__ == "__main__":
    unittest.main()
