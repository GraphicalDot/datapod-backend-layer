# from setuptools import find_packages, setup, Command


# # Package meta-data.
# NAME = 'Datapod'
# DESCRIPTION = 'One stop solution for your digital privacy'
# URL = 'https://github.com/me/myproject'
# EMAIL = 'me@example.com'
# AUTHOR = 'Datapod Team'
# REQUIRES_PYTHON = '>=3.6.0'
# VERSION = '0.1.0'
# # What packages are required for this module to be executed?
# REQUIRED = [
#     # 'requests', 'maya', 'records',
# ]

# # What packages are optional?
# EXTRAS = {
#     # 'fancy feature': ['django'],
# }

# setup(
#     name=NAME,
#     version=0.1,
#     description=DESCRIPTION,
#     long_description=DESCRIPTION,
#     long_description_content_type='text/markdown',
#     author=AUTHOR,
#     author_email=EMAIL,
#     python_requires=REQUIRES_PYTHON,
#     url=URL,
#     #packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
#     # If your package is a single module, use this instead of 'packages':
#     py_modules=['mypackage'],

#     # entry_points={
#     #     'console_scripts': ['mycli=mymodule:cli'],
#     # },
#     install_requires=REQUIRED,
#     extras_require=EXTRAS,
#     include_package_data=True,
#     license='MIT',
#     classifiers=[
#         # Trove classifiers
#         # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
#         'License :: OSI Approved :: MIT License',
#         'Programming Language :: Python',
#         'Programming Language :: Python :: 3',
#         'Programming Language :: Python :: 3.6',
#         'Programming Language :: Python :: Implementation :: CPython',
#         'Programming Language :: Python :: Implementation :: PyPy'
#     ],
#     entry_points={
#           'console_scripts': [
#               'my_project = my_project.__main__:main'
#           ]
#       },
#     # $ setup.py publish support.
#     # cmdclass={
#     #     'upload': UploadCommand,
#     # },
# )



import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os", 'encodings', 'asyncio'], "excludes": ["tkinter"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "Datapod",
        version = "0.1",
        description = "My GUI application!",
        options = {"build_exe": build_exe_options},
        executables = [Executable("application.py", base=base)])