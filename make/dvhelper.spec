# -*- mode: python ; coding: utf-8 -*-
import os
import glob


def find_mo_files():
	mo_files = []
	for mo_file in glob.glob('i18n/**/*.mo', recursive=True):
		dest_path = os.path.dirname(mo_file)
		file_path = os.path.join('..', mo_file)
		mo_files.append((file_path, dest_path))

	return mo_files

a = Analysis(
	[os.path.join('..', 'dvhelper.py')],
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
	version='version_info.txt',
	icon='icon.ico',
)
