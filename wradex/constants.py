# coding: utf-8

__all__ = [
    'WRADEX_DIR',
    'WRADEX_CONFIG',
    '_WRADEX_CONFIG',
]

# standard library
from pathlib import Path

# dependent packages
import wradex

# local constants
WRADEX_DIR = Path('~', '.wradex').expanduser()
WRADEX_CONFIG  = Path(WRADEX_DIR, 'config.yaml')
_WRADEX_CONFIG = Path(*wradex.__path__, 'data', 'config.yaml')
