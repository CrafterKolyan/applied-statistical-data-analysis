import os
import re
import sys
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import repeat

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors.execute import CellExecutionError


def find_all_notebooks(path):
  ipynb_regex = re.compile(r".*\.ipynb")
  ipynb_checkpoints_regex = re.compile(r"(^|/)\.ipynb_checkpoints")
  notebooks = []
  for address, dirs, files in os.walk(PROJECT_DIRECTORY, topdown=True):
    dirs[:] = [directory for directory in dirs if not ipynb_checkpoints_regex.match(directory)]
    notebooks.extend([os.path.join(address, x) for x in files if ipynb_regex.match(x)])
  return notebooks


def run_notebook(path, preprocessor):
  print(f"Executing {path}", end="")
  result = True
  with open(path, 'r', encoding='utf-8') as notebook_file:
    notebook = nbformat.read(notebook_file, as_version=nbformat.NO_CONVERT)

  initial_notebook = copy.deepcopy(notebook)

  try:
    preprocessor.preprocess(notebook, {'metadata': {'path': os.path.dirname(path)}})
  except CellExecutionError as e:
    result = False
    print(" FAIL!", "CHANGED!" if notebook != initial_notebook else "")
    print(e)
  else:
    print(" OK!", "CHANGED!" if notebook != initial_notebook else "")
  sys.stdout.flush()

  with open(path, 'w', encoding='utf-8') as notebook_file:
    nbformat.write(notebook, notebook_file)
  return result


PROJECT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
notebooks = find_all_notebooks(PROJECT_DIRECTORY)
execute_preprocessor = ExecutePreprocessor(timeout=600, kernel_name='python3')

exit_code = 0
for notebook in notebooks:
  result = run_notebook(notebook, execute_preprocessor)
  if not result:
    exit_code = 1

sys.exit(exit_code)
