# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import Mock
import json

from tsuru.plugins import ProcfileWatcher

from honcho.procfile import Procfile


class ProcfileWatcherTest(TestCase):
    def test_add_watcher(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.circus_client = Mock()
        name = "name"
        cmd = "cmd"
        options = json.dumps({
            "command": "add",
            "properties": {
            "cmd":  cmd,
            "name": name,
            "args": [],
            "options": {
                "copy_env": True,
                "working_dir": "/home/application/current",
                "stderr_stream": {"class": "tsuru.stream.Stream"},
                "stdout_stream": {"class": "tsuru.stream.Stream"},
            },
            "start": True,
        }})
        plugin.add_watcher(name=name, cmd=cmd)
        plugin.circus_client.call.assert_called_with(options)

    def test_remove_watcher(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        name = "name"
        plugin.remove_watcher(name=name)
        plugin.call.assert_called_with("rm", name=name)

    def test_commands(self):
        plugin = ProcfileWatcher("", "", 1)
        result = Mock()
        result.return_value = {"statuses": {}}
        plugin.call = result
        procfile = Procfile('web: gunicorn -b 0.0.0.0:8080 abyss.wsgi\n')
        to_add, to_remove = plugin.commands(procfile)
        plugin.call.assert_called_with("status")
