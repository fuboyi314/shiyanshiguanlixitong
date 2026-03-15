from __future__ import annotations

from copy import deepcopy
from typing import Dict


DEFAULT_FIELD_MAPPINGS: Dict[str, Dict[str, str]] = {
    "theory": {
        "class_name": "班级",
        "course_name": "课程",
        "teacher": "教师",
        "weekday": "星期",
        "start_period": "开始节次",
        "end_period": "结束节次",
        "weeks": "周次",
        "semester": "学期",
    },
    "lab": {
        "lab_id": "实验室编号",
        "lab_name": "实验室名称",
        "capacity": "容量",
        "campus": "校区",
        "supported_courses": "可用课程",
    },
    "task": {
        "task_id": "任务编号",
        "class_name": "班级",
        "course_name": "课程",
        "project_name": "实验项目",
        "student_count": "人数",
        "duration_periods": "时长节次",
        "expected_week": "期望周",
        "expected_weekday": "期望星期",
        "teacher": "教师",
        "notes": "备注",
    },
}


def get_default_field_mappings() -> Dict[str, Dict[str, str]]:
    """返回可安全修改的默认映射副本。"""

    return deepcopy(DEFAULT_FIELD_MAPPINGS)


def merge_user_field_mappings(user_mappings: dict | None) -> Dict[str, Dict[str, str]]:
    """将 UI 提供的字段映射增量覆盖到默认配置。"""

    merged = get_default_field_mappings()
    if not user_mappings:
        return merged

    for category, mapping in user_mappings.items():
        if category not in merged or not isinstance(mapping, dict):
            continue
        for canonical_field, excel_column in mapping.items():
            if canonical_field in merged[category] and excel_column:
                merged[category][canonical_field] = str(excel_column).strip()

    return merged
