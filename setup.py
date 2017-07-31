import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["pygame"], 
    "excludes": ["tkinter", "numpy"],
    "include_files": ["textures", "music", "data"]
    }

# GUI applications require a different base on Windows (the default is for a
# console application).
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name = "pyTetris",
    version = "1.1.7",
    description = "Python Tetris clone",
    options = {"build_exe": build_exe_options},
    executables = [Executable("tetris.py", base = base)])
