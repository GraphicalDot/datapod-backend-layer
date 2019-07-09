from PyInstaller.utils.hooks import exec_statement, collect_submodules

strptime_data_file = exec_statement(
"import inspect; import _strptime; print(inspect.getfile(_strptime))"
)

datas = [ (strptime_data_file, ".") ]

hiddenimports = collect_submodules('dateparser')