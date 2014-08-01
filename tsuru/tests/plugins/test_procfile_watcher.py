# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import Mock, patch
import os.path

from tsuru.plugins import ProcfileWatcher, WatcherCreationError

from honcho.procfile import Procfile


class ProcfileWatcherTest(TestCase):
    def build_options(self, name):
        return {
            "env": {"port": "8888", "PORT": "8888"},
            "copy_env": True,
            "working_dir": "/home/application/current",
            "stderr_stream": {
                "class": "tsuru.stream.Stream",
                "watcher_name": name
            },
            "stdout_stream": {
                "class": "tsuru.stream.Stream",
                "watcher_name": name
            },
            "uid": "ubuntu",
            "gid": "ubuntu",
        }

    def test_handle_recv(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.reload_procfile = Mock()
        plugin.handle_recv(None)
        plugin.reload_procfile.assert_called_once()

    @patch("time.sleep")
    def test_handle_recv_retries(self, sleep):
        calls = {"c": 0}

        def reload():
            calls["c"] += 1
            if calls["c"] == 1:
                raise WatcherCreationError()
        mock = Mock()
        mock.side_effect = reload
        plugin = ProcfileWatcher("", "", 1)
        plugin.reload_procfile = mock
        plugin.handle_recv(None)
        plugin.reload_procfile.assert_called()
        sleep.assert_called_once_with(1)

    def test_add_watcher(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        plugin.call.return_value = {"status": "ok"}
        plugin.envs = lambda: {}
        plugin.circus_client = Mock()
        name = "name"
        cmd = "cmd"
        options = self.build_options(name)
        plugin.add_watcher(name=name, cmd=cmd)
        plugin.call.assert_called_with("add", cmd=cmd, name=name,
                                       options=options, start=True,
                                       waiting=True)

    def test_add_watcher_creation_error_none_status(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        plugin.call.return_value = None
        plugin.envs = lambda: {}
        plugin.circus_client = Mock()
        name = "name"
        cmd = "cmd"
        with self.assertRaises(WatcherCreationError):
            plugin.add_watcher(name=name, cmd=cmd)

    def test_add_watcher_creation_error_not_ok_status(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        plugin.call.return_value = {"status": "error"}
        plugin.envs = lambda: {}
        plugin.circus_client = Mock()
        name = "name"
        cmd = "cmd"
        with self.assertRaises(WatcherCreationError):
            plugin.add_watcher(name=name, cmd=cmd)

    def test_add_watcher_creation_error_not_dict(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        plugin.call.return_value = 10
        plugin.envs = lambda: {}
        plugin.circus_client = Mock()
        name = "name"
        cmd = "cmd"
        with self.assertRaises(WatcherCreationError):
            plugin.add_watcher(name=name, cmd=cmd)

    def test_commands(self):
        plugin = ProcfileWatcher("", "", 1)
        result = Mock()
        result.return_value = {"statuses": {}}
        plugin.call = result
        procfile = Procfile('web: gunicorn -b 0.0.0.0:8080 abyss.wsgi\n')
        plugin.commands(procfile)
        plugin.call.assert_called_with("status")

    def test_commands_ignore_plugin(self):
        result = Mock()
        result.return_value = {"statuses":
                               {"plugin:tsuru-circus-ProcfileWatcher": "ok"}}
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = result
        procfile = Procfile('web: gunicorn -b 0.0.0.0:8080 abyss.wsgi\n')
        to_add = plugin.commands(procfile)
        self.assertEqual(set(["web"]), to_add)

    def test_reload_procfile_add_new_cmds(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.procfile_path = os.path.join(os.path.dirname(__file__),
                                            "testdata/Procfile1")
        plugin.circus_client = Mock()
        plugin.envs = lambda: {}
        plugin.call = Mock()
        plugin.call.return_value = {"statuses": {}, "status": "ok"}
        plugin.reload_procfile()
        options = self.build_options("name")
        plugin.call.assert_called_wit("add", cmd="cmd", name="name",
                                      options=options, start=True,
                                      waiting=True)

    def test_should_add_cmds_with_environ(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        plugin.call.return_value = {"status": "ok"}
        plugin.envs = lambda: {}
        plugin.circus_client = Mock()
        name = "name"
        cmd = "echo $port"
        options = self.build_options(name)
        plugin.add_watcher(name=name, cmd=cmd)
        cmd = cmd.replace("$port", "8888")
        plugin.call.assert_called_with("add", cmd=cmd, name=name,
                                       options=options, start=True,
                                       waiting=True)

    def test_should_add_cmds_with_environ_upercase(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        plugin.call.return_value = {"status": "ok"}
        plugin.envs = lambda: {}
        plugin.circus_client = Mock()
        name = "name"
        cmd = "echo $PORT"
        options = self.build_options(name)
        plugin.add_watcher(name=name, cmd=cmd)
        cmd = cmd.replace("$PORT", "8888")
        plugin.call.assert_called_with("add", cmd=cmd, name=name,
                                       options=options, start=True,
                                       waiting=True)

    def test_should_add_cmds_with_environ_with_braces(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        plugin.call.return_value = {"status": "ok"}
        plugin.envs = lambda: {}
        name = "name"
        cmd = "echo ${PORT}"
        options = self.build_options(name)
        plugin.add_watcher(name=name, cmd=cmd)
        cmd = cmd.replace("${PORT}", "8888")
        plugin.call.assert_called_with("add", cmd=cmd, name=name,
                                       options=options, start=True,
                                       waiting=True)
