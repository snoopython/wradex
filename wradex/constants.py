# coding: utf-8

__all__ = [
    'WRADEX_DIR',
    'WRADEX_CONF',
    '_WRADEX_CONF',
]

# standard library
from pathlib import Path

# dependent packages
import wradex

# local constants
WRADEX_DIR   = Path('~', '.wradex').expanduser()
WRADEX_CONF  = Path(WRADEX_DIR, 'config.yaml')
_WRADEX_CONF = Path(*wradex.__path__, 'data', 'config.yaml')
