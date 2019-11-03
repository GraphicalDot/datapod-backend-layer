
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
from PyInstaller.utils.hooks import collect_data_files, eval_statement, collect_submodules

import datasources

datas = collect_submodules('sentry_sdk')

a = Analysis( [ 'application.py'],
             pathex=['', '/home/feynman/Programs/datapod-backend-layer/Application'],
             binaries=[],
             datas=[],
             hiddenimports=['engineio.async_eventlet', '_striptime', 'engineio.async_gevent'] + datas ,
             hookspath=['pyinstaller_hooks'],
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
          name='Datapod_ubuntu',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False , icon='datapod.ico')


