from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


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
}


def load_ui_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    if not path.exists():
        return json.loads(json.dumps(DEFAULT_CONFIG))
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_ui_config(config: dict, path: Path = DEFAULT_CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=2)


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

    def do_GET(self) -> None:
        if self.path == "/api/config":
            self._send_json(load_ui_config())
            return
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/config":
            self._send_json({"error": "Not Found"}, status=HTTPStatus.NOT_FOUND)
            return

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
