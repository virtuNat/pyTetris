import sys
from cx_Freeze import setup, Executable

# Dependency list.
build_exe_options = {
    "packages": ["pygame"], 
    "excludes": ["tkinter", "numpy"],
    "include_files": ["textures", "music", "data"]
    }
# Base for GUI apps on Windows.
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name = "pyTetris",
    version = "1.1.8",
    description = "Python Tetris clone",
    options = {"build_exe": build_exe_options},
    executables = [Executable("__main__.py", base = base)])
