# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import Mock
import os

from tsuru.plugins import ApprcWatcher


def create_fake_call(status_return):
    kw = []

    def fake_call(command, *args, **kwargs):
        if command == "status":
            return status_return
        elif command == "set":
            kw.append(kwargs)
            return {"set": "ok"}
    return fake_call, kw


class ApprcWatcherTest(TestCase):
    def test_add_envs(self):
        plugin = ApprcWatcher("", "", 1)
        plugin.call = Mock()
        plugin.add_envs(name="name", envs={"foo": "bar"})
        plugin.call.assert_called_with("set",
                                       name="name",
                                       options={"env": {"foo": "bar"}})

    def test_look_after_add_envs(self):
        sr = {"statuses": {"name": "name", "cmd": "cmd"}}
        fake_call, kw = create_fake_call(sr)
        plugin = ApprcWatcher("", "", 1)
        plugin.call = fake_call
        plugin.apprc = os.path.join(os.path.dirname(__file__),
                                    "testdata/apprc")
        plugin.look_after()
        env = {'VAR1': 'value-1', 'port': '8888', 'VAR2': 'value2'}
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
        env = {'VAR1': 'value-1', 'port': '8888', 'VAR2': 'value2'}
        expected = [
            {"name": "name", "options": {"env": env}},
        ]
        self.assertEqual(expected, kw)
