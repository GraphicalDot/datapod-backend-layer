# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
from PyInstaller.utils.hooks import collect_data_files, eval_statement, collect_submodules

datas = collect_submodules('sentry_sdk')

a = Analysis(['application.py'],
             pathex=[
               '/home/feynman/Programs/datapod-backend-layer/Application'],
             binaries=[],
             datas=[
                 ('/home/feynman/Programs/datapod-backend-layer/Application/datasources/', './datasources/'),
                 ('/home/feynman/Programs/datapod-backend-layer/Application/EncryptionModule/', './EncryptionModule/'),
             ],
             hiddenimports=['engineio.async_eventlet', '_striptime', 'engineio.async_gevent', 'humanize', 'PIL.Image', 'dateparser', 'paramiko',
              'pyparsing', 'github', 'csv', 'mnemonic', 'bip32utils', 'lxml.html.clean', 'bleach', 'mailbox', 'imaplib', 'geopy']  + datas,
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
          name='backendbinary',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False , icon='datapod.ico')



