# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import Mock
import json
import os.path

from tsuru.plugins import ProcfileWatcher

from honcho.procfile import Procfile


class ProcfileWatcherTest(TestCase):
    def test_add_watcher(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.envs = lambda: {}
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
                "env": {"port": "8888"},
                "copy_env": True,
                "working_dir": "/home/application/current",
                "stderr_stream": {"class": "tsuru.stream.Stream"},
                "stdout_stream": {"class": "tsuru.stream.Stream"},
                "uid": "ubuntu",
            },
            "start": True,
        }})
        plugin.add_watcher(name=name, cmd=cmd)
        plugin.circus_client.call.assert_called_with(options)

    def test_remove_watchers(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        plugin.call.return_value = {"statuses": {"name": ""}}
        plugin.remove_watchers()
        plugin.call.assert_called_with("rm", name="name")

    def test_envs(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.apprc = os.path.join(os.path.dirname(__file__), "testdata/apprc")
        envs = plugin.envs()
        expected = {
            "VAR1": "value-1",
            "VAR2": "value2",
        }
        self.assertDictEqual(expected, envs)
