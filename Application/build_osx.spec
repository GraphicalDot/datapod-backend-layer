# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


__VERSION__ = "0.3.3"

APPNAME = f"datapod-osx-{__VERSION__}"

import distutils
if distutils.distutils_path.endswith('__init__.py'):
    distutils.distutils_path = os.path.dirname(distutils.distutils_path)



from PyInstaller.utils.hooks import collect_data_files, eval_statement, collect_submodules

datas = collect_submodules( 'sentry_sdk')


a = Analysis(['application.py'],
             pathex=['/Users/kaali/Programs/datapod-backend-layer/Application'],
             binaries=[],
             datas=[
                 ('/Users/kaali/Programs/datapod-backend-layer/Application/datasources/', './datasources/'),
                 ('/Users/kaali/Programs/datapod-backend-layer/Application/EncryptionModule/', './EncryptionModule/'),
                ('/Users/kaali/Programs/datapod-backend-layer/Application/permissions/', './permissions/'),
             ],
               hiddenimports=['engineio.async_eventlet', '_striptime', 'engineio.async_gevent', 'humanize', 
                            'PIL.Image', 'dateparser', 'paramiko', 'playhouse.sqlite_ext', 'asyncinit',
                            'pyparsing', 'github', 'csv', 'mnemonic', 'bip32utils', 
                            'lxml.html.clean', 'bleach', 'mailbox', 'imaplib', 'geopy', "boto3"]  + datas,
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
          name=APP,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False , icon='datapod.ico')
app = BUNDLE(exe,
             name='backendbinary.app',
             icon='datapod.ico',
             bundle_identifier=None)
