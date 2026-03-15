from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

import pandas as pd

from data_models.models import Lab, LabTask, TheoryClassSlot


class ExcelLoadError(Exception):
    """Excel 读取与字段标准化异常。"""


def _require_columns(df: pd.DataFrame, expected_columns: Iterable[str], sheet_name: str) -> None:
    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        raise ExcelLoadError(f"sheet[{sheet_name}] 缺少列: {', '.join(missing)}")


def _split_to_list(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [item.strip() for item in str(value).replace("；", ",").replace(";", ",").split(",") if item.strip()]


def _parse_weeks(value: object) -> list[int]:
    if pd.isna(value):
        return []
    raw = str(value).replace("，", ",").replace("；", ",")
    weeks: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start > end:
                start, end = end, start
            weeks.extend(range(start, end + 1))
        else:
            weeks.append(int(part))
    return sorted(set(weeks))


def _to_int(value: object, field_name: str, row_index: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError) as exc:
        raise ExcelLoadError(f"第 {row_index + 2} 行字段[{field_name}] 不是有效整数: {value}") from exc


def _to_optional_int(value: object, field_name: str, row_index: int) -> int | None:
    if pd.isna(value) or value == "":
        return None
    return _to_int(value, field_name, row_index)


def load_theory_class_slots(excel_path: str, field_mapping: dict[str, str], sheet_name: str = 0) -> list[TheoryClassSlot]:
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    _require_columns(df, field_mapping.values(), str(sheet_name))

    results: list[TheoryClassSlot] = []
    for idx, row in df.iterrows():
        try:
            slot = TheoryClassSlot(
                class_name=str(row[field_mapping["class_name"]]).strip(),
                course_name=str(row[field_mapping["course_name"]]).strip(),
                teacher=str(row[field_mapping["teacher"]]).strip(),
                weekday=_to_int(row[field_mapping["weekday"]], "weekday", idx),
                start_period=_to_int(row[field_mapping["start_period"]], "start_period", idx),
                end_period=_to_int(row[field_mapping["end_period"]], "end_period", idx),
                weeks=_parse_weeks(row[field_mapping["weeks"]]),
                semester=(
                    str(row[field_mapping["semester"]]).strip()
                    if "semester" in field_mapping and not pd.isna(row[field_mapping["semester"]])
                    else None
                ),
            )
            results.append(slot)
        except KeyError as exc:
            raise ExcelLoadError(f"理论课字段映射缺失: {exc}") from exc
    return results


def load_labs(excel_path: str, field_mapping: dict[str, str], sheet_name: str = 0) -> list[Lab]:
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    _require_columns(df, field_mapping.values(), str(sheet_name))

    labs: list[Lab] = []
    for idx, row in df.iterrows():
        lab = Lab(
            lab_id=str(row[field_mapping["lab_id"]]).strip(),
            lab_name=str(row[field_mapping["lab_name"]]).strip(),
            capacity=_to_int(row[field_mapping["capacity"]], "capacity", idx),
            campus=(
                str(row[field_mapping["campus"]]).strip()
                if "campus" in field_mapping and not pd.isna(row[field_mapping["campus"]])
                else None
            ),
            supported_courses=_split_to_list(row[field_mapping["supported_courses"]]),
        )
        labs.append(lab)
    return labs


def load_lab_tasks(excel_path: str, field_mapping: dict[str, str], sheet_name: str = 0) -> list[LabTask]:
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    _require_columns(df, field_mapping.values(), str(sheet_name))

    tasks: list[LabTask] = []
    for idx, row in df.iterrows():
        task = LabTask(
            task_id=str(row[field_mapping["task_id"]]).strip(),
            class_name=str(row[field_mapping["class_name"]]).strip(),
            course_name=str(row[field_mapping["course_name"]]).strip(),
            project_name=str(row[field_mapping["project_name"]]).strip(),
            student_count=_to_int(row[field_mapping["student_count"]], "student_count", idx),
            duration_periods=_to_int(row[field_mapping["duration_periods"]], "duration_periods", idx),
            expected_week=_to_optional_int(row[field_mapping["expected_week"]], "expected_week", idx),
            expected_weekday=_to_optional_int(row[field_mapping["expected_weekday"]], "expected_weekday", idx),
            teacher=(
                str(row[field_mapping["teacher"]]).strip()
                if "teacher" in field_mapping and not pd.isna(row[field_mapping["teacher"]])
                else None
            ),
            notes=(
                str(row[field_mapping["notes"]]).strip()
                if "notes" in field_mapping and not pd.isna(row[field_mapping["notes"]])
                else None
            ),
        )
        tasks.append(task)
    return tasks


def dataclass_list_to_records(items: list[object]) -> list[dict]:
    """辅助函数：将 dataclass 列表转换为可序列化 records。"""

    return [asdict(item) for item in items]
