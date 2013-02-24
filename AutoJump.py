#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Faster **Goto Anything** in large projects through
integration with joelthelion/autojump.
"""

from subprocess import check_output, CalledProcessError
import re

def check_autojump_installation():
  try:
    check_output(args = ["autojump"])

    # if command not found, there'll be exception raised
    return True
  except:
    return False
  else:
    return False
  return False

def load_autojump_database():
  # Load autojump database
  try:
    # execute `autojump --stat` and parse results
    ajdb = check_output(args = ["autojump", "--stat"])
    regex = re.compile("\d+.\d+:\s*(.+)")
    aj_dirs = [ x.strip() for x in regex.findall(ajdb) ]

    if len(aj_dirs) > 0:
      return aj_dirs
    else:
      return None
  except CalledProcessError:
    pass
  else:
    pass
  return None

def add_to_autojump_database(path):
  # Add entry to autojump database
  if len(path) == 0:
    return

  try:
    # execute `autojump -a path`
    check_output(args = ["autojump", "-a %s" % path])
  except CalledProcessError:
    pass
  else:
    pass

if __name__ == "__main__":
  if not check_autojump_installation():
    print ("Please install autojump first.\n"
      "Download and install autojump: https://github.com/joelthelion/autojump")
    exit()

  print load_autojump_database()
  #add_to_autojump_database("muhaha")