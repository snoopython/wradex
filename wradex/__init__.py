# coding: utf-8

# dependent packages
import shutil

# submodules
from .constants import *

if not WRADEX_DIR.exists():
    WRADEX_DIR.mkdir()
    shutil.copy(str(_WRADEX_CONFIG), str(WRADEX_DIR))

from .radex import *

# clean local
del constants
del radex
del shutil
