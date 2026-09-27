import os
import sys

# point to local libraries
libs_path = os.path.join(os.path.dirname(__file__), "libraries")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

from .suutego import *