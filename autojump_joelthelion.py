#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoJump: Open a Recent File or a File in a Visited Folder

This library contains functions used to connect with joelthelion/autojump.
"""

import subprocess
import re


def run_shell_cmd(cmd):
    """
    Run shell command and return (is_successful, output)
    """
    proc = subprocess.Popen(args=[cmd],
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
        return []

    # Remove the "total key weight" and "stored directories" entries
    db_content, __ = ajdb.split("________________________________________")

    # Parse results
    regex = re.compile("\d+.\d+:\s*(.+)")
    aj_dirs = [x.strip() for x in regex.findall(db_content)]
    aj_dirs.reverse()

    if len(aj_dirs) > 0:
        return aj_dirs
    else:
        return []


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
