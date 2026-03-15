from __future__ import annotations

import argparse
import cgi
import json
import tempfile
from dataclasses import asdict
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from data_models.models import ScheduledItem, UnscheduledItem
from utils.config import get_default_field_mappings


BASE_DIR = Path(__file__).resolve().parent.parent
WEBUI_DIR = BASE_DIR / "webui"
DATA_DIR = BASE_DIR / "data"
DEFAULT_CONFIG_PATH = DATA_DIR / "ui_config.json"


DEFAULT_CONFIG: dict = {
    "semester": {
        "semester_name": "2025-2026-1",
        "start_date": "2025-09-01",
        "total_weeks": 16,
        "periods_per_day": 10,
        "working_days": [1, 2, 3, 4, 5],
        "holidays": [],
    },
    "theory_slots": [],
    "labs": [],
    "lab_tasks": [],
    "schedule_result": {"scheduled_items": [], "unscheduled_items": []},
}


def load_ui_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    if not path.exists():
        return json.loads(json.dumps(DEFAULT_CONFIG))
    with path.open("r", encoding="utf-8") as file:
        loaded = json.load(file)
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    config.update(loaded)
    if "schedule_result" not in config:
        config["schedule_result"] = {"scheduled_items": [], "unscheduled_items": []}
    return config


def save_ui_config(config: dict, path: Path = DEFAULT_CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=2)


def _import_preview(kind: str, file_path: str) -> tuple[list[dict], dict]:
    from services.excel_loader import (
        ExcelLoadError,
        dataclass_list_to_records,
        load_lab_tasks,
        load_labs,
        load_theory_class_slots,
    )

    mappings = get_default_field_mappings()
    target = {
        "theory": ("theory_slots", load_theory_class_slots),
        "lab": ("labs", load_labs),
        "task": ("lab_tasks", load_lab_tasks),
    }
    target_field, loader = target[kind]
    missing_fields: list[str] = []
    invalid_values: list[str] = []
    records: list[dict] = []

    try:
        items = loader(file_path, mappings[kind])
        records = dataclass_list_to_records(items)
    except ExcelLoadError as exc:
        error_text = str(exc)
        if "缺少列" in error_text:
            missing_fields = [col.strip() for col in error_text.split(":", 1)[-1].split(",") if col.strip()]
        else:
            invalid_values.append(error_text)

    return records, {
        "target": target_field,
        "read_count": len(records),
        "missing_fields": missing_fields,
        "invalid_values": invalid_values,
    }


def _overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return not (a_end < b_start or b_end < a_start)


def run_demo_schedule(config: dict) -> tuple[list[ScheduledItem], list[UnscheduledItem]]:
    labs = config.get("labs", [])
    tasks = config.get("lab_tasks", [])
    theory_slots = config.get("theory_slots", [])

    occupied: dict[tuple[str, int, int], list[tuple[int, int]]] = {}
    scheduled: list[ScheduledItem] = []
    unscheduled: list[UnscheduledItem] = []

    for task in tasks:
        task_id = str(task.get("task_id", "")).strip()
        class_name = str(task.get("class_name", "")).strip()
        course_name = str(task.get("course_name", "")).strip()
        project_name = str(task.get("project_name", "")).strip()
        student_count = int(task.get("student_count", 0) or 0)
        duration = int(task.get("duration_periods", 0) or 0)
        expected_week = task.get("expected_week") or 1
        expected_weekday = task.get("expected_weekday") or 1
        teacher = task.get("teacher")

        if duration <= 0:
            unscheduled.append(
                UnscheduledItem(
                    task_id=task_id,
                    class_name=class_name,
                    course_name=course_name,
                    project_name=project_name,
                    reason="任务时长无效",
                    teacher=teacher,
                )
            )
            continue

        matched_by_course = [
            lab
            for lab in labs
            if not lab.get("supported_courses") or course_name in (lab.get("supported_courses") or [])
        ]
        if not matched_by_course:
            unscheduled.append(
                UnscheduledItem(
                    task_id=task_id,
                    class_name=class_name,
                    course_name=course_name,
                    project_name=project_name,
                    reason="无课程匹配实验室",
                    teacher=teacher,
                )
            )
            continue

        capacity_labs = [lab for lab in matched_by_course if int(lab.get("capacity", 0) or 0) >= student_count]
        if not capacity_labs:
            unscheduled.append(
                UnscheduledItem(
                    task_id=task_id,
                    class_name=class_name,
                    course_name=course_name,
                    project_name=project_name,
                    reason="无容量满足实验室",
                    teacher=teacher,
                )
            )
            continue

        theory_ref = next((slot for slot in theory_slots if slot.get("class_name") == class_name and slot.get("course_name") == course_name), None)
        start_period = int(theory_ref.get("start_period", 1) if theory_ref else 1)
        end_period = start_period + duration - 1

        selected = None
        for lab in capacity_labs:
            key = (lab.get("lab_id"), int(expected_week), int(expected_weekday))
            periods = occupied.get(key, [])
            if all(not _overlap(start_period, end_period, p_start, p_end) for p_start, p_end in periods):
                selected = lab
                occupied.setdefault(key, []).append((start_period, end_period))
                break

        if not selected:
            unscheduled.append(
                UnscheduledItem(
                    task_id=task_id,
                    class_name=class_name,
                    course_name=course_name,
                    project_name=project_name,
                    reason="期望周/星期无空闲实验室",
                    teacher=teacher,
                )
            )
            continue

        scheduled.append(
            ScheduledItem(
                task_id=task_id,
                class_name=class_name,
                course_name=course_name,
                project_name=project_name,
                lab_id=str(selected.get("lab_id", "")),
                lab_name=str(selected.get("lab_name", "")),
                week=int(expected_week),
                weekday=int(expected_weekday),
                start_period=start_period,
                end_period=end_period,
                teacher=teacher,
            )
        )

    return scheduled, unscheduled


class ConfigHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEBUI_DIR), **kwargs)

    def _send_json(self, body: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_file(self, file_path: Path, filename: str) -> None:
        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _save_uploaded_file(self) -> tuple[str, Path]:
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("Content-Type", "")},
        )
        uploaded = form["file"]
        if not getattr(uploaded, "file", None):
            raise ValueError("未接收到上传文件")

        suffix = Path(uploaded.filename or "uploaded.xlsx").suffix or ".xlsx"
        temp_file = Path(tempfile.mkstemp(prefix="webui-upload-", suffix=suffix)[1])
        temp_file.write_bytes(uploaded.file.read())
        return str(uploaded.filename), temp_file

    def do_GET(self) -> None:
        if self.path == "/api/config":
            self._send_json(load_ui_config())
            return

        if self.path.startswith("/api/template/"):
            kind = self.path.split("/")[-1]
            sample_map = {
                "theory": BASE_DIR / "sample_data" / "theory_schedule.xlsx",
                "lab": BASE_DIR / "sample_data" / "labs.xlsx",
                "task": BASE_DIR / "sample_data" / "lab_tasks.xlsx",
            }
            target = sample_map.get(kind)
            if not target:
                self._send_json({"error": "模板类型不存在"}, status=HTTPStatus.NOT_FOUND)
                return
            if not target.exists():
                self._send_json({"error": "模板文件不存在，请先执行 sample_data/generate_sample_data.py"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_file(target, target.name)
            return

        if self.path == "/api/schedule/export":
            config = load_ui_config()
            scheduled = [ScheduledItem(**item) for item in config.get("schedule_result", {}).get("scheduled_items", [])]
            unscheduled = [UnscheduledItem(**item) for item in config.get("schedule_result", {}).get("unscheduled_items", [])]
            out_file = Path(tempfile.mkstemp(prefix="schedule-result-", suffix=".xlsx")[1])
            from services.exporter import export_schedule_result

            export_schedule_result(str(out_file), scheduled, unscheduled)
            self._send_file(out_file, "schedule_result.xlsx")
            out_file.unlink(missing_ok=True)
            return

        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/config":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(content_length)
                payload = json.loads(raw.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("payload must be object")
                save_ui_config(payload)
                self._send_json({"message": "saved"})
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, status=HTTPStatus.BAD_REQUEST)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path.startswith("/api/import/"):
            kind = self.path.split("/")[-1]
            if kind not in {"theory", "lab", "task"}:
                self._send_json({"error": "导入类型不存在"}, status=HTTPStatus.NOT_FOUND)
                return
            try:
                _, temp_path = self._save_uploaded_file()
                records, preview = _import_preview(kind, str(temp_path))
                if not preview["missing_fields"] and not preview["invalid_values"]:
                    config = load_ui_config()
                    config[preview["target"]] = records
                    save_ui_config(config)
                self._send_json(preview)
            except Exception as exc:  # noqa: BLE001
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            finally:
                if "temp_path" in locals():
                    Path(temp_path).unlink(missing_ok=True)
            return

        if self.path == "/api/schedule/run":
            config = load_ui_config()
            scheduled, unscheduled = run_demo_schedule(config)
            config["schedule_result"] = {
                "scheduled_items": [asdict(item) for item in scheduled],
                "unscheduled_items": [asdict(item) for item in unscheduled],
            }
            save_ui_config(config)
            self._send_json(
                {
                    "scheduled_count": len(scheduled),
                    "unscheduled_count": len(unscheduled),
                    "scheduled_items": [asdict(item) for item in scheduled],
                    "unscheduled_items": [asdict(item) for item in unscheduled],
                }
            )
            return

        self._send_json({"error": "Not Found"}, status=HTTPStatus.NOT_FOUND)


def run_server(port: int) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), ConfigHTTPRequestHandler)
    print(f"Web UI 启动成功: http://127.0.0.1:{port}")
    print("按 Ctrl+C 结束服务")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="实验室排课本地 Web UI")
    parser.add_argument("--port", type=int, default=8000, help="服务端口，默认 8000")
    args = parser.parse_args()
    run_server(args.port)


if __name__ == "__main__":
    main()
