# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
import os

from tsuru.plugins import ApprcWatcher

PATH_OUTPUT = {
    "status": "ok",
    "options": {
        "max_retry": 5,
        "env": {
            "PATH": "/usr/bin:/bin:/sbin",
            "SOMETHING": "adios",
        },
    },
}

NOPATH_OUTPUT = {
    "status": "ok",
    "options": {
        "max_retry": 5,
        "env": {"SOMETHING": "adios"},
    },
}


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


class ApprcWatcherTest(TestCase):
    def test_add_envs(self):
        plugin = ApprcWatcher("", "", 1)
        plugin.call, kw = create_fake_call(None)
        plugin.add_envs(name="name", envs={"foo": "bar"})
        expected = [
            {"name": "name", "options": {"env": {"foo": "bar"}}},
        ]
        self.assertEqual(expected, kw)

    def test_add_envs_preserves_path(self):
        plugin = ApprcWatcher("", "", 1)
        plugin.call, kw = create_fake_call(None, PATH_OUTPUT)
        plugin.add_envs(name="name", envs={"foo": "bar"})
        expected = [
            {"name": "name",
             "options": {"env": {"foo": "bar",
                                 "PATH": PATH_OUTPUT["options"]["env"]["PATH"]}}},
        ]
        self.assertEqual(expected, kw)

    def test_add_envs_may_override_path(self):
        plugin = ApprcWatcher("", "", 1)
        plugin.call, kw = create_fake_call(None, PATH_OUTPUT)
        plugin.add_envs(name="name", envs={"foo": "bar", "PATH": "/bin"})
        expected = [
            {"name": "name",
             "options": {"env": {"foo": "bar", "PATH": "/bin"}}},
        ]
        self.assertEqual(expected, kw)

    def test_add_envs_dont_call_set_when_variables_dont_change(self):
        plugin = ApprcWatcher("", "", 1)
        plugin.call, kw = create_fake_call(None)
        plugin.add_envs(name="name", envs=NOPATH_OUTPUT["options"]["env"])
        self.assertEqual([], kw)

    def test_add_envs_dont_call_set_when_variables_dont_change_and_path_is_defined(self):
        plugin = ApprcWatcher("", "", 1)
        plugin.call, kw = create_fake_call(None, PATH_OUTPUT)
        plugin.add_envs(name="name", envs=PATH_OUTPUT["options"]["env"])
        self.assertEqual([], kw)

    def test_look_after_add_envs(self):
        sr = {"statuses": {"name": "name", "cmd": "cmd"}}
        fake_call, kw = create_fake_call(sr)
        plugin = ApprcWatcher("", "", 1)
        plugin.call = fake_call
        plugin.apprc = os.path.join(os.path.dirname(__file__),
                                    "testdata/apprc")
        plugin.look_after()
        env = {"VAR1": "value-1", "port": "8888", "VAR2": "value2"}
        expected = [
            {"name": "cmd", "options": {"env": env}},
            {"name": "name", "options": {"env": env}},
        ]
        self.assertEqual(expected, sorted(kw, key=lambda x: x["name"]))

    def test_look_after_skips_plugins(self):
        sr = {"statuses": {"name": "name",
                           "plugin:tsuru-circus-ApprcWatcher": "ok"}}
        fake_call, kw = create_fake_call(sr)
        plugin = ApprcWatcher("", "", 1)
        plugin.call = fake_call
        plugin.apprc = os.path.join(os.path.dirname(__file__),
                                    "testdata/apprc")
        plugin.look_after()
        env = {"VAR1": "value-1", "port": "8888", "VAR2": "value2"}
        expected = [
            {"name": "name", "options": {"env": env}},
        ]
        self.assertEqual(expected, kw)
