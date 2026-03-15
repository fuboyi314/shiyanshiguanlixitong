from datetime import date
import unittest

from data_models.models import (
    Lab,
    LabProject,
    LabTask,
    ScheduledItem,
    SemesterConfig,
    TheoryClassSlot,
    UnscheduledItem,
)


class TestDataModels(unittest.TestCase):
    def test_can_create_all_core_models(self) -> None:
        theory = TheoryClassSlot(
            class_name="计科231",
            course_name="数据结构",
            teacher="张老师",
            weekday=1,
            start_period=1,
            end_period=2,
            weeks=[1, 2, 3],
            semester="2025-2026-1",
        )
        self.assertEqual(theory.class_name, "计科231")

        lab = Lab(
            lab_id="LAB-A101",
            lab_name="计算机基础实验室",
            capacity=50,
            campus="主校区",
            supported_courses=["数据结构"],
        )
        self.assertEqual(lab.capacity, 50)

        project = LabProject(
            project_id="P001",
            project_name="图算法综合实验",
            default_duration_periods=2,
            required_capacity=40,
            preferred_labs=["LAB-A101"],
        )
        self.assertEqual(project.default_duration_periods, 2)

        task = LabTask(
            task_id="TASK-001",
            class_name="计科231",
            course_name="数据结构",
            project_name="图算法综合实验",
            student_count=46,
            duration_periods=2,
            expected_week=6,
            expected_weekday=2,
            teacher="张老师",
            notes="需要投影",
        )
        self.assertEqual(task.student_count, 46)

        semester = SemesterConfig(
            semester_name="2025-2026-1",
            start_date=date(2025, 9, 1),
            total_weeks=16,
            periods_per_day=10,
        )
        self.assertEqual(semester.working_days, [1, 2, 3, 4, 5])

        scheduled = ScheduledItem(
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
        )
        self.assertEqual(scheduled.end_period, 4)

        unscheduled = UnscheduledItem(
            task_id="TASK-999",
            class_name="计科999",
            course_name="未知课程",
            project_name="未知实验",
            reason="无可用实验室",
        )
        self.assertEqual(unscheduled.reason, "无可用实验室")


if __name__ == "__main__":
    unittest.main()
