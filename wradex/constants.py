# coding: utf-8

__all__ = [
    'WRADEX_DIR',
    'WRADEX_CONFIG',
    '_WRADEX_CONFIG',
]

# standard library
import os
from pathlib import Path

# dependent packages
import wradex

# local constants
if 'WRADEX_DIR' in os.environ:
    path = os.environ.get('WRADEX_DIR')
    WRADEX_DIR = Path(path).expanduser()
else:
    WRADEX_DIR = Path.home() / '.wradex'

WRADEX_CONFIG  = Path(WRADEX_DIR, 'config.yaml')
_WRADEX_CONFIG = Path(*wradex.__path__, 'data', 'config.yaml')
