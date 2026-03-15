from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(slots=True)
class TheoryClassSlot:
    """标准化后的理论课时隙数据。"""

    class_name: str
    course_name: str
    teacher: str
    weekday: int
    start_period: int
    end_period: int
    weeks: list[int] = field(default_factory=list)
    semester: Optional[str] = None


@dataclass(slots=True)
class Lab:
    """实验室基础信息。"""

    lab_id: str
    lab_name: str
    capacity: int
    campus: Optional[str] = None
    supported_courses: list[str] = field(default_factory=list)


@dataclass(slots=True)
class LabProject:
    """实验课程/项目定义（可作为 LabCourse 使用）。"""

    project_id: str
    project_name: str
    default_duration_periods: int
    required_capacity: int = 0
    preferred_labs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class LabTask:
    """待安排的实验任务。"""

    task_id: str
    class_name: str
    course_name: str
    project_name: str
    student_count: int
    duration_periods: int
    expected_week: Optional[int] = None
    expected_weekday: Optional[int] = None
    teacher: Optional[str] = None
    notes: Optional[str] = None


@dataclass(slots=True)
class SemesterConfig:
    """学期级配置。"""

    semester_name: str
    start_date: date
    total_weeks: int
    periods_per_day: int
    working_days: list[int] = field(default_factory=lambda: [1, 2, 3, 4, 5])


@dataclass(slots=True)
class ScheduledItem:
    """已排课结果项。"""

    task_id: str
    class_name: str
    course_name: str
    project_name: str
    lab_id: str
    lab_name: str
    week: int
    weekday: int
    start_period: int
    end_period: int
    teacher: Optional[str] = None


@dataclass(slots=True)
class UnscheduledItem:
    """未排课结果项。"""

    task_id: str
    class_name: str
    course_name: str
    project_name: str
    reason: str
    teacher: Optional[str] = None
