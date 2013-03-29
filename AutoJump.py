#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoJump: Open a Recent File or a File in a Visited Folder

Works with joelthelion/autojump:
  https://github.com/joelthelion/autojump
"""

import json
import os
import re
import sublime
import sublime_plugin
import autojump_joelthelion

base_name = "AutoJump.sublime-settings"

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

def remove_nonexisting_entries(view):
  """
  Purge recent file list
  """
  update_autojump_database = load_setting(view, "update_autojump_database", True)
  if update_autojump_database:
    autojump_joelthelion.purge_autojump_database()

  recent_files = load_setting(view, "recent_files", None)
  if recent_files is None:
    return

  for path in recent_files:
    if not os.path.isfile(path):
      recent_files.remove(path)

  global_settings = sublime.load_settings(base_name)
  global_settings.set("recent_files", recent_files)

  sublime.save_settings(base_name)

def load_recent_files(view):
  """
  Load recent file list from AutoJump package setting & Session.sublime_session
  """
  # Load recent file list from AutoJump package setting
  recent_files = load_setting(view, "recent_files", None)
  if recent_files is None:
    recent_files = []

  # Load recent file list from Session.sublime_session
  session_dir = os.path.join( os.path.dirname( sublime.packages_path() ), "Settings")
  session_file = os.path.join(session_dir, "Session.sublime_session")
  if os.path.isfile(session_file):
    with open(session_file, 'r') as f:
      file_content = f.read()

    if len(file_content) > 0:
      regex = re.compile("\"file_history\":.*?\[.*?\]",re.DOTALL)
      if regex.search(file_content):
        try:
          file_history_strs = regex.findall(file_content)[0]
          for file_history_str in file_history_strs:
            session_data = json.loads("{%s}" % file_history_str)

            if session_data:
              for path in session_data["file_history"]:
                if not path in recent_files:
                  recent_files.append(path)
        except:
          pass
        finally:
          pass

  return recent_files

class AutojumpOpenRecentFileCommand(sublime_plugin.WindowCommand):
  def run(self):
    """
    Load recent files from settings
    """
    recent_files = load_recent_files(self.window.active_view())

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

    if os.path.exists(picked_file):
      self.window.open_file(picked_file)
    else:
      sublime.error_message("File %s does not exist." % picked_file)
      remove_nonexisting_entries(self.window.active_view())

class AutojumpTraverseVisitedFolderCommand(sublime_plugin.WindowCommand):
  def run(self):
    """
    List recently accessed folders for users to select
    """

    results = []

    # if we have installed joelthelion/autojump, use its database
    if autojump_joelthelion.autojump_installed():
      results = autojump_joelthelion.load_autojump_database()

    # we also extract recently accessed folder paths from our recent_files
    recent_files = load_recent_files(self.window.active_view())
    for recent_file in recent_files:
      folder_path = os.path.dirname(recent_file)
      if not folder_path in results:
        results.append( os.path.dirname(recent_file) )

    user_path = os.path.expanduser("~")
    if not user_path in results:
      results.append(user_path)

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
      sublime.error_message("Folder %s does not exist." % self.picked_folder)
      remove_nonexisting_entries()
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
      autojump_joelthelion.add_to_autojump_database(path)

    # update package setting: recent_files
    recent_files = load_setting(view, "recent_files", None)
    if recent_files is None:
      recent_files = []
    else:
      if current_file_name in recent_files:
        recent_files.remove(current_file_name)
    recent_files.insert(0, current_file_name)

    global_settings = sublime.load_settings(base_name)
    global_settings.set("recent_files", recent_files)

    sublime.save_settings(base_name)

  def on_load(self, view):
    self.update_database(view)

  def on_post_save(self, view):
    self.update_database(view)