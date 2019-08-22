# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
import distutils
if distutils.distutils_path.endswith('__init__.py'):
    distutils.distutils_path = os.path.dirname(distutils.distutils_path)

a = Analysis(['../application.py'],
             pathex=['/Users/kaali/Programs/datapod-backend-layer/Application/Executables'],
             binaries=[],
             datas=[],
             hiddenimports=['_striptime'],
             hookspath=['../pyinstaller_hooks'],
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
          name='Datapodmac',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False , icon='datapod.ico')
app = BUNDLE(exe,
             name='Datapodmac.app',
             icon='datapod.ico',
             bundle_identifier=None)
