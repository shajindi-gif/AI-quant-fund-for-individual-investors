from __future__ import annotations

from pathlib import Path
import yaml

from src.validation import validate_config


def load_config(config_path: str = 'config.yaml') -> dict:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f'Config file not found: {config_path}')
    with path.open('r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    validate_config(config)
    return config
