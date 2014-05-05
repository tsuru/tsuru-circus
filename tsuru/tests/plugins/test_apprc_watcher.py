# Copyright 2013 tsuru-circus authors. All rights reserved.
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
            kw.append(kwargs)
            return {"set": "ok"}
        elif command == "options":
            return options_return
    return fake_call, kw


class ApprcWatcherTest(unittest.TestCase):
    def test_add_envs(self):
        plugin = ApprcWatcher("", "", 1)
        plugin.call, kw = create_fake_call(None)
        plugin.add_envs(name="name", envs={"foo": "bar"})
        env = copy.deepcopy(os.environ)
        env["foo"] = "bar"
        expected = [{"name": "name", "options": {"env": env}}]
        self.assertEqual(expected, kw)

    def test_add_envs_may_override_os_environ(self):
        os.environ["SOMETHING_UNKNOWN"] = "123"
        self.addCleanup(remove_env, "SOMETHING_UNKNOWN")
        plugin = ApprcWatcher("", "", 1)
        plugin.call, kw = create_fake_call(None)
        plugin.add_envs(name="name", envs={"foo": "bar",
                                           "SOMETHING_UNKNOWN": "456"})
        env = copy.deepcopy(os.environ)
        env["SOMETHING_UNKNOWN"] = "456"
        env["foo"] = "bar"
        expected = [{"name": "name", "options": {"env": env}}]
        self.assertEqual(expected, kw)

    def test_add_envs_dont_call_set_when_variables_dont_change(self):
        plugin = ApprcWatcher("", "", 1)
        envs = copy.deepcopy(NOPATH_OUTPUT)
        envs["options"]["env"].update(os.environ)
        plugin.call, kw = create_fake_call(None, envs)
        plugin.add_envs(name="name", envs=NOPATH_OUTPUT["options"]["env"])
        self.assertEqual([], kw)

    def test_add_envs_override_environs(self):
        plugin = ApprcWatcher("", "", 1)
        envs = copy.deepcopy(NOPATH_OUTPUT)
        envs["options"]["env"]["foo"] = "foo"
        plugin.call, kw = create_fake_call(None, envs)
        plugin.add_envs(name="name", envs={"foo": "bar"})
        env = copy.deepcopy(os.environ)
        env["foo"] = "bar"
        expected = [{"name": "name", "options": {"env": env}}]
        self.assertEqual(expected, kw)

    def test_add_env_ignores_PYTHONPATH_from_os_environ(self):
        os.environ["PYTHONPATH"] = "/home/user/python"
        self.addCleanup(remove_env, "PYTHONPATH")
        plugin = ApprcWatcher("", "", 1)
        plugin.call, kw = create_fake_call(None)
        plugin.add_envs(name="name", envs={"foo": "bar"})
        env = copy.deepcopy(os.environ)
        env["foo"] = "bar"
        del env["PYTHONPATH"]
        expected = [{"name": "name", "options": {"env": env}}]
        self.assertEqual(expected, kw)

    def test_add_env_doesnt_ignore_PYTHONPATH_from_apprc(self):
        plugin = ApprcWatcher("", "", 1)
        plugin.call, kw = create_fake_call(None)
        plugin.add_envs(name="name", envs={"foo": "bar",
                                           "PYTHONPATH": "/usr/lib/python"})
        env = copy.deepcopy(os.environ)
        env["foo"] = "bar"
        env["PYTHONPATH"] = "/usr/lib/python"
        expected = [{"name": "name", "options": {"env": env}}]
        self.assertEqual(expected, kw)

    def test_reload_env_add_envs(self):
        sr = {"statuses": {"name": "name", "cmd": "cmd"}}
        fake_call, kw = create_fake_call(sr)
        plugin = ApprcWatcher("", "", 1)
        plugin.call = fake_call
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
        self.assertEqual(expected, sorted(kw, key=lambda x: x["name"]))

    def test_reload_env_skips_plugins(self):
        sr = {"statuses": {"name": "name",
                           "plugin:tsuru-circus-ApprcWatcher": "ok"}}
        fake_call, kw = create_fake_call(sr)
        plugin = ApprcWatcher("", "", 1)
        plugin.call = fake_call
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
            {"name": "name", "options": {"env": env}},
        ]
        self.assertEqual(expected, kw)
