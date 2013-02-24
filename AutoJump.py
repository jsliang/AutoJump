#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Faster **Goto Anything** in large projects through
integration with joelthelion/autojump.
"""

import os
import re
import sublime
import sublime_plugin
import subprocess


def run_shell_cmd(cmd):
  proc = subprocess.Popen(args = [cmd],
                          shell=True,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
  (stdoutdata, stderrdata) = proc.communicate()
  if proc.poll():
    return (False, None)
  else:
    return (True, stdoutdata)

def check_autojump_installation():
  (success, __) = run_shell_cmd("autojump")
  if success:
    return True
  return False

def load_autojump_database():
  # Load autojump database
  # execute `autojump --stat` and parse results
  (success, ajdb) = run_shell_cmd("autojump --stat")
  if not success:
    return None

  regex = re.compile("\d+.\d+:\s*(.+)")
  aj_dirs = [ x.strip() for x in regex.findall(ajdb) ]

  if len(aj_dirs) > 0:
    return sorted(aj_dirs)
  else:
    return None

def add_to_autojump_database(path):
  # Add entry to autojump database
  if len(path) == 0:
    return
  run_shell_cmd('autojump -a "%s"' % path)

class AutojumpLoadDatabaseCommand(sublime_plugin.WindowCommand):
  def on_done():
    # TODO: traverse subfolder
    pass

  def run(self):
    if not check_autojump_installation():
      sublime.error_message("Please install autojump first.\n"
        "Download and install autojump: https://github.com/joelthelion/autojump")
      return

    results = load_autojump_database()

    if not results:
      sublime.error_message("No entries found in autojump database."
        "Please use `cd` command to visit any directory first.")
      return

    self.window.show_quick_panel(results, self.on_done)

class AutojumpUpdateDatabase(sublime_plugin.EventListener):
  def on_load(self, view):
    path = os.path.dirname( view.file_name() )
    add_to_autojump_database(path)

  def on_post_save(self, view):
    path = os.path.dirname( view.file_name() )
    add_to_autojump_database(path)
