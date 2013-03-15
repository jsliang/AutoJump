#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoJump: Open a Recent File or a File in a Visited Folder

Works with joelthelion/autojump:
  https://github.com/joelthelion/autojump
"""

import os
import re
import sublime
import sublime_plugin
import subprocess

base_name = "AutoJump.sublime-settings"

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

    global_settings = sublime.load_settings(base_name)

    return view.settings().get(setting_name, global_settings.get(setting_name, default_value))

class AutojumpOpenRecentFileCommand(sublime_plugin.WindowCommand):
  def run(self):
    """
    Load recent files from settings
    """

    recent_files = load_setting(self.window.active_view(), "recent_files", None)
    if recent_files is None:
      recent_files = []

    self.recent_files = []
    for recent_file in recent_files:
      file_basename = os.path.basename(recent_file)
      file_fullname = recent_file
      self.recent_files.append( [file_basename, file_fullname] )

    self.window.show_quick_panel(self.recent_files, self.on_done)

  def on_done(self, picked):
    """
    Open selected file
    """
    if picked == -1:
        return

    picked_file = self.recent_files[picked][1]

    self.window.open_file(picked_file)

class AutojumpLoadDatabaseCommand(sublime_plugin.WindowCommand):
  def run(self):
    """
    List folders in autojump database for users to select
    """
    if not autojump_installed():
      return

    results = load_autojump_database()

    if not results:
      return

    self.results = []
    for path in results:
      folder_name = os.path.split(path)[1]
      folder_path = path
      self.results.append( [folder_name, folder_path] )

    self.window.show_quick_panel(self.results, self.traverse_subfolder)

  def traverse_subfolder(self, picked):
    """
    Traverse selected folder
    """
    if picked == -1:
        return

    self.picked_folder = self.results[picked][1]
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

    if picked == -1:
        return

    open_path = os.path.join(self.picked_folder, self.file_list[picked])
    self.window.open_file(open_path)

class AutojumpUpdateDatabase(sublime_plugin.EventListener):
  """
  Update package setting & autojump database on file load and after file save.
  """

  def update_database(self, view):
    current_file_name = view.file_name()

    # update autojump database
    update_autojump_database = load_setting(view, "update_autojump_database", True)
    if update_autojump_database:
      path = os.path.dirname(current_file_name)
      add_to_autojump_database(path)

    # update package setting: recent_files
    recent_files = load_setting(view, "recent_files", None)
    if recent_files is None:
      recent_files = []
    else:
      if current_file_name in recent_files:
        recent_files.remove(current_file_name)
    recent_files.insert(0, current_file_name)

    max_recent_files = load_setting(view, "max_recent_files", 30)
    recent_files = recent_files[0:max_recent_files]

    global_settings = sublime.load_settings(base_name)
    global_settings.set("recent_files", recent_files)

    sublime.save_settings(base_name)

  def on_load(self, view):
    self.update_database(view)

  def on_post_save(self, view):
    self.update_database(view)