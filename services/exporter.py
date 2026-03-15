from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict

import pandas as pd

from data_models.models import ScheduledItem, UnscheduledItem


def _build_lab_utilization(scheduled_items: list[ScheduledItem]) -> pd.DataFrame:
    usage_counter: dict[str, int] = defaultdict(int)
    lab_name_map: dict[str, str] = {}

    for item in scheduled_items:
        periods = item.end_period - item.start_period + 1
        usage_counter[item.lab_id] += max(periods, 0)
        lab_name_map[item.lab_id] = item.lab_name

    records = [
        {"lab_id": lab_id, "lab_name": lab_name_map.get(lab_id), "used_periods": used_periods}
        for lab_id, used_periods in usage_counter.items()
    ]
    return pd.DataFrame(records).sort_values(by=["used_periods", "lab_id"], ascending=[False, True])


def _build_class_statistics(scheduled_items: list[ScheduledItem], unscheduled_items: list[UnscheduledItem]) -> pd.DataFrame:
    scheduled_by_class: dict[str, int] = defaultdict(int)
    unscheduled_by_class: dict[str, int] = defaultdict(int)

    for item in scheduled_items:
        scheduled_by_class[item.class_name] += 1
    for item in unscheduled_items:
        unscheduled_by_class[item.class_name] += 1

    class_names = sorted(set(scheduled_by_class) | set(unscheduled_by_class))
    records = []
    for class_name in class_names:
        done = scheduled_by_class[class_name]
        todo = unscheduled_by_class[class_name]
        total = done + todo
        rate = round(done / total, 4) if total else 0
        records.append(
            {
                "class_name": class_name,
                "scheduled_count": done,
                "unscheduled_count": todo,
                "schedule_rate": rate,
            }
        )

    return pd.DataFrame(records).sort_values(by=["schedule_rate", "class_name"], ascending=[False, True])


def export_schedule_result(
    output_path: str,
    scheduled_items: list[ScheduledItem],
    unscheduled_items: list[UnscheduledItem],
) -> None:
    """导出多 sheet 排课结果。"""

    scheduled_df = pd.DataFrame([asdict(item) for item in scheduled_items])
    unscheduled_df = pd.DataFrame([asdict(item) for item in unscheduled_items])
    lab_utilization_df = _build_lab_utilization(scheduled_items)
    class_statistics_df = _build_class_statistics(scheduled_items, unscheduled_items)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        scheduled_df.to_excel(writer, sheet_name="已排课", index=False)
        unscheduled_df.to_excel(writer, sheet_name="未排课", index=False)
        lab_utilization_df.to_excel(writer, sheet_name="实验室利用率", index=False)
        class_statistics_df.to_excel(writer, sheet_name="班级统计", index=False)
