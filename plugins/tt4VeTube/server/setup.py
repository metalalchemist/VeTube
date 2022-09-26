# create Windows build from CX_Freece
import sys
from cx_Freeze import setup, Executable 
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

build_exe_options = dict(
	build_exe="dist",
	optimize=1,
	include_msvcr=True,
	)

executables = [
    Executable('app.py', base=base, targetName="app")
]

setup(name="Voice-API",
      version="1.0",
      description="",
      options = {"build_exe": build_exe_options},
      executables=executables
      )
