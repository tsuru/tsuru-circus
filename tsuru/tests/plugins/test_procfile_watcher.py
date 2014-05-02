# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import Mock, patch
import os.path

from tsuru.plugins import ProcfileWatcher

from honcho.procfile import Procfile


class ProcfileWatcherTest(TestCase):
    def build_options(self, name, cmd):
        return {
            "command": "add",
            "properties": {
                "cmd": cmd,
                "name": name,
                "args": [],
                "options": {
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
                },
                "start": True,
                "priority": 2,
            },
        }

    def test_add_watcher(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.envs = lambda: {}
        plugin.circus_client = Mock()
        name = "name"
        cmd = "cmd"
        options = self.build_options(name, cmd)
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
        to_add, to_remove, to_change = plugin.commands(procfile)
        plugin.call.assert_called_with("status")

    def test_commands_ignore_plugin(self):
        result = Mock()
        result.return_value = {"statuses":
                               {"plugin:tsuru-circus-ProcfileWatcher": "ok"}}
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = result
        procfile = Procfile('web: gunicorn -b 0.0.0.0:8080 abyss.wsgi\n')
        to_add, to_remove, to_change = plugin.commands(procfile)
        self.assertEqual(set(["web"]), to_add)
        self.assertEqual(set([]), to_remove)
        self.assertEqual({}, to_change)

    def test_reload_procfile_add_new_cmds(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.procfile_path = os.path.join(os.path.dirname(__file__),
                                            "testdata/Procfile1")
        plugin.circus_client = Mock()
        plugin.envs = lambda: {}
        plugin.call = Mock()
        plugin.call.return_value = {"statuses": {}}
        plugin.reload_procfile()
        options = self.build_options("name", "cmd")
        plugin.circus_client.call.assert_called_with(options)

    def test_reload_procfile_remove_old_cmds(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        plugin.call.return_value = {"statuses": {"name": "name", "cmd": "cmd"}}
        plugin.procfile_path = os.path.join(os.path.dirname(__file__),
                                            "testdata/Procfile2")
        plugin.reload_procfile()
        plugin.call.assert_called_with("rm", name="name")

    def test_reload_procfile_update_cmds(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        plugin.call.return_value = {"statuses": {"name": "name", "cmd": "cmd"}}
        plugin.get_cmd = Mock()
        plugin.get_cmd.return_value = "cmd"
        plugin.procfile_path = os.path.join(os.path.dirname(__file__),
                                            "testdata/Procfile3")
        plugin.reload_procfile()
        plugin.get_cmd.assert_called_with("name")
        plugin.call.assert_called_with("set",
                                       name="name",
                                       options={'cmd': 'cmd2'})

    def test_get_cmd(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        plugin.call.return_value = {"options": {"cmd": "ble"}}
        cmd = plugin.get_cmd("name")
        self.assertEqual("ble", cmd)
        plugin.call.assert_called_with("get",
                                       name="name",
                                       keys=["cmd"])

    def test_should_replace_cmds_with_environ(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.envs = lambda: {}
        plugin.circus_client = Mock()
        name = "name"
        cmd = "echo $port"
        options = self.build_options(name, "echo 8888")
        plugin.add_watcher(name=name, cmd=cmd)
        plugin.circus_client.call.assert_called_with(options)

    def test_should_replace_cmds_with_environ_upercase(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.envs = lambda: {}
        plugin.circus_client = Mock()
        name = "name"
        cmd = "echo $PORT"
        options = self.build_options(name, "echo 8888")
        plugin.add_watcher(name=name, cmd=cmd)
        plugin.circus_client.call.assert_called_with(options)

    def test_should_replace_cmds_with_environ_with_braces(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.envs = lambda: {}
        plugin.circus_client = Mock()
        name = "name"
        cmd = "echo ${PORT}"
        options = self.build_options(name, "echo 8888")
        plugin.add_watcher(name=name, cmd=cmd)
        plugin.circus_client.call.assert_called_with(options)

    @patch("tsuru.common.load_envs")
    def test_change_cmd_should_replace_cmds_with_environ(self, load_envs):
        load_envs.return_value = {"BLE": "bla"}
        plugin = ProcfileWatcher("", "", 1)
        plugin.envs = lambda: {}
        plugin.call = Mock()
        plugin.port = 8888
        name = "name"
        cmd = "echo ${PORT} ${port} ${BLE}"
        plugin.change_cmd(name=name, cmd=cmd)
        plugin.call.assert_called_with('set',
                                       options={'cmd': 'echo 8888 8888 bla'},
                                       name=name)

    def test_commands_dont_remove_tsuru_hooks_watcher(self):
        plugin = ProcfileWatcher("", "", 1)
        result = Mock()
        result.return_value = {"statuses": {"tsuru-hooks": ""}}
        plugin.call = result
        procfile = Procfile('web: gunicorn -b 0.0.0.0:8080 abyss.wsgi\n')
        to_add, to_remove, to_change = plugin.commands(procfile)
        self.assertNotIn("tsuru-hooks", to_remove)
