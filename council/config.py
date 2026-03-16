"""
Configuration for Council backend.
"""
import json
import os
import socket
from pathlib import Path
from typing import Optional

DATA_DIR = Path.home() / ".council"
PORT_FILE = str(DATA_DIR / "port")


def _find_free_port(start: int = 8090, end: int = 9000) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free port found in range {start}-{end}")


def write_port_file(port: int, path: str = PORT_FILE):
    DATA_DIR.mkdir(exist_ok=True, parents=True)
    Path(path).write_text(str(port))


def read_port_file(path: str = PORT_FILE) -> Optional[int]:
    try:
        return int(Path(path).read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


def cleanup_port_file(path: str = PORT_FILE):
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass


class Config:
    def __init__(self):
        self.host = os.environ.get("COUNCIL_HOST", "127.0.0.1")
        self.port = int(os.environ.get("COUNCIL_PORT", "0"))  # 0 = auto
        self.db_path = os.environ.get(
            "COUNCIL_DB",
            str(DATA_DIR / "council.db"),
        )
        self.debug = os.environ.get("COUNCIL_DEBUG", "0") == "1"

    def resolve_port(self) -> int:
        if self.port == 0:
            self.port = _find_free_port()
        return self.port
