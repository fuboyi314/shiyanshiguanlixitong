from __future__ import annotations

from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path(__file__).resolve().parent


def _write_theory_schedule() -> None:
    df = pd.DataFrame(
        [
            {
                "班级": "计科231",
                "课程": "数据结构",
                "教师": "张老师",
                "星期": 1,
                "开始节次": 1,
                "结束节次": 2,
                "周次": "1-16",
                "学期": "2025-2026-1",
            },
            {
                "班级": "计科232",
                "课程": "数据库原理",
                "教师": "李老师",
                "星期": 3,
                "开始节次": 3,
                "结束节次": 4,
                "周次": "1-16",
                "学期": "2025-2026-1",
            },
        ]
    )
    df.to_excel(OUTPUT_DIR / "theory_schedule.xlsx", index=False)


def _write_labs() -> None:
    df = pd.DataFrame(
        [
            {"实验室编号": "LAB-A101", "实验室名称": "计算机基础实验室", "容量": 50, "校区": "主校区", "可用课程": "数据结构,数据库原理"},
            {"实验室编号": "LAB-B203", "实验室名称": "软件工程实验室", "容量": 45, "校区": "主校区", "可用课程": "软件工程,数据库原理"},
            {"实验室编号": "LAB-C301", "实验室名称": "AI实验室", "容量": 40, "校区": "创新校区", "可用课程": "机器学习,深度学习"},
        ]
    )
    df.to_excel(OUTPUT_DIR / "labs.xlsx", index=False)


def _write_lab_tasks() -> None:
    df = pd.DataFrame(
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
                "备注": "需要投影设备",
            },
            {
                "任务编号": "TASK-002",
                "班级": "计科232",
                "课程": "数据库原理",
                "实验项目": "SQL优化实验",
                "人数": 42,
                "时长节次": 2,
                "期望周": 8,
                "期望星期": 4,
                "教师": "李老师",
                "备注": "需要MySQL环境",
            },
            {
                "任务编号": "TASK-003",
                "班级": "计科233",
                "课程": "软件工程",
                "实验项目": "需求分析建模",
                "人数": 38,
                "时长节次": 3,
                "期望周": 10,
                "期望星期": 5,
                "教师": "王老师",
                "备注": "分组演示",
            },
        ]
    )
    df.to_excel(OUTPUT_DIR / "lab_tasks.xlsx", index=False)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_theory_schedule()
    _write_labs()
    _write_lab_tasks()
    print(f"示例数据已生成到: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
