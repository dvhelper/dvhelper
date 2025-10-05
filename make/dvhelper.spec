# -*- mode: python ; coding: utf-8 -*-
import os


def find_mo_files():
    mo_files = []

    for root, _, files in os.walk('i18n'):
        for file in files:
            _, ext = os.path.splitext(file)

            if ext == '.mo':
                file_path = os.path.relpath(os.path.join(root, file), '.')
                dest_path = os.path.dirname(file_path)
                file_path = os.path.join('..', file_path)
                mo_files.append((file_path, dest_path))
    return mo_files

a = Analysis(
    ['..\\dvhelper.py'],
    pathex=[],
    binaries=[],
    datas=find_mo_files(),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='dvhelper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    codesign_identity=None,
    entitlements_file=None,
    version='.\\version_info.txt',
    icon=['.\\icon.ico'],
)
