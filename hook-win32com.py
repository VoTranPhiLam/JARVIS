
# hook-win32com.py
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('win32com')
hiddenimports += collect_submodules('win32com')
