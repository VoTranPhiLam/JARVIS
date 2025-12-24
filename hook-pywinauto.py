
# hook-pywinauto.py
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('pywinauto')
hiddenimports += collect_submodules('pywinauto')
