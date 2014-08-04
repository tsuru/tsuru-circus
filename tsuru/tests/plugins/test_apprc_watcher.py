# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import copy
import os
import unittest

from tsuru.plugins import ApprcWatcher

NOPATH_OUTPUT = {
    "status": "ok",
    "options": {
        "max_retry": 5,
        "env": {"SOMETHING": "adios"},
    },
}


def remove_env(name):
    del os.environ[name]


def create_fake_call(status_return, options_return=NOPATH_OUTPUT):
    kw = []

    def fake_call(command, *args, **kwargs):
        if command == "status":
            return status_return
        elif command == "set":
            kw.append({"cmd": command, "args": kwargs})
            return {"set": "ok"}
        elif command in ("start", "stop"):
            kw.append({"cmd": command, "args": kwargs})
        elif command == "options":
            return options_return
    return fake_call, kw


class ApprcWatcherTest(unittest.TestCase):
    def test_init(self):
        plugin = ApprcWatcher("", "", 1, loop_rate="10",
                              apprc="/etc/apprc", port="8080")
        self.assertEqual(10, plugin.loop_rate)
        self.assertEqual("/etc/apprc", plugin.apprc)
        self.assertEqual("8080", plugin.port)

    def test_init_default_config_values(self):
        plugin = ApprcWatcher("", "", 1)
        self.assertEqual(3, plugin.loop_rate)
        self.assertEqual("/home/application/apprc", plugin.apprc)
        self.assertEqual("8888", plugin.port)

    def test_add_envs(self):
        plugin = ApprcWatcher("", "", 1)
        fake_call, kw = create_fake_call(None)
        plugin.call = fake_call
        plugin.cast = fake_call
        plugin.add_envs(name="name", envs={"foo": "bar"})
        env = copy.deepcopy(os.environ)
        env["foo"] = "bar"
        expected = [{"cmd": "stop", "args": {"name": "name", "waiting": True}},
                    {"cmd": "set", "args": {"name": "name",
                                            "options": {"env": env}}},
                    {"cmd": "start", "args": {"name": "name",
                                              "waiting": True}}]
        self.assertEqual(expected, kw)

    def test_add_envs_may_override_os_environ(self):
        os.environ["SOMETHING_UNKNOWN"] = "123"
        self.addCleanup(remove_env, "SOMETHING_UNKNOWN")
        plugin = ApprcWatcher("", "", 1)
        fake_call, kw = create_fake_call(None)
        plugin.call = fake_call
        plugin.cast = fake_call
        plugin.add_envs(name="name", envs={"foo": "bar",
                                           "SOMETHING_UNKNOWN": "456"})
        env = copy.deepcopy(os.environ)
        env["SOMETHING_UNKNOWN"] = "456"
        env["foo"] = "bar"
        expected = [{"cmd": "stop", "args": {"name": "name", "waiting": True}},
                    {"cmd": "set", "args": {"name": "name",
                                            "options": {"env": env}}},
                    {"cmd": "start", "args": {"name": "name",
                                              "waiting": True}}]
        self.assertEqual(expected, kw)

    def test_add_envs_dont_call_set_when_variables_dont_change(self):
        plugin = ApprcWatcher("", "", 1)
        envs = copy.deepcopy(NOPATH_OUTPUT)
        envs["options"]["env"].update(os.environ)
        fake_call, kw = create_fake_call(None, envs)
        plugin.call = fake_call
        plugin.cast = fake_call
        plugin.add_envs(name="name", envs=NOPATH_OUTPUT["options"]["env"])
        self.assertEqual([], kw)

    def test_add_envs_override_environs(self):
        plugin = ApprcWatcher("", "", 1)
        envs = copy.deepcopy(NOPATH_OUTPUT)
        envs["options"]["env"]["foo"] = "foo"
        fake_call, kw = create_fake_call(None, envs)
        plugin.call = fake_call
        plugin.cast = fake_call
        plugin.add_envs(name="name", envs={"foo": "bar"})
        env = copy.deepcopy(os.environ)
        env["foo"] = "bar"
        expected = [{"cmd": "stop", "args": {"name": "name", "waiting": True}},
                    {"cmd": "set", "args": {"name": "name",
                                            "options": {"env": env}}},
                    {"cmd": "start", "args": {"name": "name",
                                              "waiting": True}}]
        self.assertEqual(expected, kw)

    def test_add_env_ignores_PYTHONPATH_from_os_environ(self):
        os.environ["PYTHONPATH"] = "/home/user/python"
        self.addCleanup(remove_env, "PYTHONPATH")
        plugin = ApprcWatcher("", "", 1)
        fake_call, kw = create_fake_call(None)
        plugin.call = fake_call
        plugin.cast = fake_call
        plugin.add_envs(name="name", envs={"foo": "bar"})
        env = copy.deepcopy(os.environ)
        env["foo"] = "bar"
        del env["PYTHONPATH"]
        expected = [{"cmd": "stop", "args": {"name": "name", "waiting": True}},
                    {"cmd": "set", "args": {"name": "name",
                                            "options": {"env": env}}},
                    {"cmd": "start", "args": {"name": "name",
                                              "waiting": True}}]
        self.assertEqual(expected, kw)

    def test_add_env_doesnt_ignore_PYTHONPATH_from_apprc(self):
        plugin = ApprcWatcher("", "", 1)
        fake_call, kw = create_fake_call(None)
        plugin.call = fake_call
        plugin.cast = fake_call
        plugin.add_envs(name="name", envs={"foo": "bar",
                                           "PYTHONPATH": "/usr/lib/python"})
        env = copy.deepcopy(os.environ)
        env["foo"] = "bar"
        env["PYTHONPATH"] = "/usr/lib/python"
        expected = [{"cmd": "stop", "args": {"name": "name", "waiting": True}},
                    {"cmd": "set", "args": {"name": "name",
                                            "options": {"env": env}}},
                    {"cmd": "start", "args": {"name": "name",
                                              "waiting": True}}]
        self.assertEqual(expected, kw)

    def test_reload_env_add_envs(self):
        sr = {"statuses": {"name": "name", "cmd": "cmd"}}
        fake_call, kw = create_fake_call(sr)
        plugin = ApprcWatcher("", "", 1)
        plugin.call = fake_call
        plugin.cast = fake_call
        plugin.apprc = os.path.join(os.path.dirname(__file__),
                                    "testdata/apprc")
        plugin.reload_env()
        env = {
            "VAR1": "value-1",
            "port": "8888",
            "VAR2": "value2",
            "PORT": "8888"
        }
        env.update(os.environ)
        expected = [
            {"name": "cmd", "options": {"env": env}},
            {"name": "name", "options": {"env": env}},
        ]
        expected = [{"cmd": "stop", "args": {"name": "cmd", "waiting": True}},
                    {"cmd": "set", "args": {"name": "cmd",
                                            "options": {"env": env}}},
                    {"cmd": "start", "args": {"name": "cmd", "waiting": True}},
                    {"cmd": "stop", "args": {"name": "name", "waiting": True}},
                    {"cmd": "set", "args": {"name": "name",
                                            "options": {"env": env}}},
                    {"cmd": "start", "args": {"name": "name",
                                              "waiting": True}}]
        self.assertEqual(expected, sorted(kw, key=lambda x: x["args"]["name"]))

    def test_reload_env_skips_plugins(self):
        sr = {"statuses": {"name": "name",
                           "plugin:tsuru-circus-ApprcWatcher": "ok"}}
        fake_call, kw = create_fake_call(sr)
        plugin = ApprcWatcher("", "", 1)
        plugin.call = fake_call
        plugin.cast = fake_call
        plugin.apprc = os.path.join(os.path.dirname(__file__),
                                    "testdata/apprc")
        plugin.reload_env()
        env = {
            "VAR1": "value-1",
            "port": "8888",
            "VAR2": "value2",
            "PORT": "8888"
        }
        env.update(os.environ)
        expected = [{"cmd": "stop", "args": {"name": "name", "waiting": True}},
                    {"cmd": "set", "args": {"name": "name",
                                            "options": {"env": env}}},
                    {"cmd": "start", "args": {"name": "name",
                                              "waiting": True}}]
        self.assertEqual(expected, kw)
