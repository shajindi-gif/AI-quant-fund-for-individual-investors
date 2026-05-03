from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(log_dir: str = "logs", log_file: str = "quant.log", level: int = logging.INFO) -> None:
    """
    Configure root logger once.

    We keep it intentionally lightweight: file + console, no external dependencies.
    """
    log_path_dir = Path(log_dir)
    log_path_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_path_dir / log_file

    root_logger = logging.getLogger()
    if root_logger.handlers:
        # Avoid duplicate handlers if `setup_logging()` is called multiple times.
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

