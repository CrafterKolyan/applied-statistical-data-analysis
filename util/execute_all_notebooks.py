#!/usr/bin/python3

import os
import re
import sys
import copy

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors.execute import CellExecutionError

import argparse


def find_all_notebooks(path, recursive=False, include_checkpoints=False):
  ipynb_regex = re.compile(r"^.*\.ipynb$")
  if not recursive:
    notebooks = [os.path.join(path, x) for x in os.listdir(path) if ipynb_regex.fullmatch(x)]
    notebooks = [x for x in notebooks if os.path.isfile(x)]
    return notebooks
  ipynb_checkpoints_regex = re.compile(r"\.ipynb_checkpoints")
  notebooks = []
  for address, dirs, files in os.walk(path, topdown=True):
    if not include_checkpoints:
      dirs[:] = [directory for directory in dirs if not ipynb_checkpoints_regex.fullmatch(directory)]
    notebooks.extend([os.path.join(address, x) for x in files if ipynb_regex.fullmatch(x)])
  return notebooks


def delete_execution_metadata(notebook):
  for cell in notebook.cells:
    if cell.cell_type == 'code':
      del cell.metadata['execution']


def run_notebook(path, preprocessor):
  print(f"Executing {path}", end="")
  result = True
  with open(path, 'r', encoding='utf-8') as notebook_file:
    notebook = nbformat.read(notebook_file, as_version=nbformat.current_nbformat)

  initial_notebook_cells = copy.deepcopy(notebook['cells'])

  try:
    preprocessor.preprocess(notebook, {'metadata': {'path': os.path.dirname(path)}})
  except CellExecutionError as e:
    result = False
    print(" FAIL!", " CHANGED!" if notebook['cells'] != initial_notebook_cells else "", sep="")
    print(e)
  else:
    print(" OK!", " CHANGED!" if notebook['cells'] != initial_notebook_cells else "", sep="")
  sys.stdout.flush()
  delete_execution_metadata(notebook)

  with open(path, 'w', encoding='utf-8') as notebook_file:
    nbformat.write(notebook, notebook_file)
  return result


def main(args):
  notebooks = []
  for folder in args.folder:
    notebooks.extend(find_all_notebooks(folder, recursive=args.recursive, include_checkpoints=args.include_checkpoints))
  notebooks = [notebook for notebook in notebooks if notebook not in args.exclude]
  execute_preprocessor = ExecutePreprocessor(timeout=args.timeout, kernel_name=args.kernel)

  exit_code = 0
  for notebook in notebooks:
    result = run_notebook(notebook, execute_preprocessor)
    if not result:
      exit_code = 1

  sys.exit(exit_code)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Execute all notebooks in folder')
  parser.add_argument('folder', type=str, nargs='+', help='folder with notebooks (default: directory where script is executed)')
  parser.add_argument('-r', '--recursive', action='store_true', help='execute notebooks in folders recursively')
  parser.add_argument('-i', '--include-checkpoints', action='store_true', help='execute notebooks from .ipynb_checkpoints folders (--recursive required)')
  parser.add_argument('-t', '--timeout', type=int, default=600, help='cell execution timeout in seconds (default: 600)')
  parser.add_argument('-k', '--kernel', type=str, default='python3', help='execution kernel (default: "python3")')
  parser.add_argument('--exclude', type=str, default=[], action='append', help='exclude file from executing')
  args = parser.parse_args()
  main(args)
