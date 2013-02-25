#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoJump: Open a File in a Visited Folder

Prerequistic: https://github.com/joelthelion/autojump
"""

import os
import re
import sublime
import sublime_plugin
import subprocess


def run_shell_cmd(cmd):
  """
  Run shell command and return (is_successful, output)
  """
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

def autojump_installed():
  """
  Check if autojump is installed.
  """
  (success, __) = run_shell_cmd("autojump")
  if success:
    return True
  return False

def load_autojump_database():
  """
  Load autojump database
  """

  # Execute `autojump --stat`
  (success, ajdb) = run_shell_cmd("autojump --stat")
  if not success:
    return None

  # Parse results
  regex = re.compile("\d+.\d+:\s*(.+)")
  aj_dirs = [ x.strip() for x in regex.findall(ajdb) ]
  aj_dirs.reverse()

  if len(aj_dirs) > 0:
    return aj_dirs
  else:
    return None

def add_to_autojump_database(path):
  """
  Add entry to autojump database
  """
  if len(path) == 0:
    return
  run_shell_cmd('autojump -a "%s"' % path)

def purge_autojump_database():
  """
  Remove entries that no longer exist
  """
  run_shell_cmd('autojump --purge')

def load_setting(view, setting_name, default_value=None):
    """
    Load Sublime settings
    """

    if len(setting_name) < 1:
        if default_value:
            return default_value
        return None

    global_settings = sublime.load_settings("AutoJump.sublime-settings")

    return view.settings().get(setting_name, global_settings.get(setting_name, default_value))

class AutojumpLoadDatabaseCommand(sublime_plugin.WindowCommand):
  def run(self):
    """
    List folders in autojump database for users to select
    """
    if not autojump_installed():
      sublime.error_message("Please install autojump first.\n"
        "Download and install autojump: https://github.com/joelthelion/autojump")
      return

    self.results = load_autojump_database()

    if not self.results:
      sublime.error_message("No entries found in autojump database."
        "Please use `cd` command to visit any directory first.")
      return

    self.window.show_quick_panel(self.results, self.traverse_subfolder)

  def traverse_subfolder(self, picked):
    """
    Traverse selected folder
    """
    if picked == -1:
        return

    self.picked_folder = self.results[picked]
    if not os.path.exists(self.picked_folder):
      sublime.error_message("Folder %s does not exists." % self.picked_folder)

      update_autojump_database = load_setting(self.window.active_view(), "update_autojump_database", True)
      if update_autojump_database:
        purge_autojump_database()

      return

    view = self.window.active_view()
    exclude_filepath_filters = load_setting(view, "exclude_filepath_filters", None)

    self.file_list = []
    for dirpath, dirnames, filenames in os.walk(self.picked_folder, followlinks=True):
      for filename in filenames:
        path_str = os.path.join(dirpath, filename)
        path_str = path_str.replace(self.picked_folder + '/', '')

        ignore = False
        for exclude_filter in exclude_filepath_filters:
          if re.search(exclude_filter, path_str):
            ignore = True

        if ignore:
          continue

        self.file_list.append(path_str)

    if len(self.file_list) > 0:
      self.file_list = sorted(self.file_list)
      self.window.show_quick_panel(self.file_list, self.on_done)
    else:
      sublime.error_message("%s is an empty folder." % self.picked_folder)

  def on_done(self, picked):
    """
    Open selected file
    """
    open_path = os.path.join(self.picked_folder, self.file_list[picked])
    self.window.open_file(open_path)

class AutojumpUpdateDatabase(sublime_plugin.EventListener):
  """
  Update autojump database on file load and after file save.
  """
  def on_load(self, view):
    update_autojump_database = load_setting(view, "update_autojump_database", True)
    if update_autojump_database:
      path = os.path.dirname( view.file_name() )
      add_to_autojump_database(path)

  def on_post_save(self, view):
    update_autojump_database = load_setting(view, "update_autojump_database", True)
    if update_autojump_database:
      path = os.path.dirname( view.file_name() )
      add_to_autojump_database(path)
