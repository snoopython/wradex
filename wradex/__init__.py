# coding: utf-8

# dependent packages
import shutil

# submodules
from .constants import *
from .radex import *

# create ~/.wradex
if not WRADEX_DIR.exists():
    WRADEX_DIR.mkdir()
    shutil.copy(_WRADEX_CONF, WRADEX_DIR)

# clean local
del shutil
