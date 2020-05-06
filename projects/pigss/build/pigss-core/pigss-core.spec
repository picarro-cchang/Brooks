# -*- mode: python ; coding: utf-8 -*-
import os
import importlib

"""
In some cases, we rely on an external package that has a configuration file
that pyinstaller cannot find as it follows imports. In this event, we'll
bundle the entire external package, so it can use any configuration files
it relies on at runtime.
"""
packages_to_include = ['aiohttp_swagger']
package_list = []
for package in packages_to_include:
    package_root = os.path.dirname(importlib.import_module(package).__file__)
    package_list.append((package_root, package))

block_cipher = None

a = Analysis(['../../back_end/pigss_runner.py'],
             pathex=[],
             binaries=[],
             datas=package_list,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='pigss-core',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
