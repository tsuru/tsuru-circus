# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import Mock
import os

from tsuru.plugins import ApprcWatcher


class ApprcWatcherTest(TestCase):
    def test_add_envs(self):
        plugin = ApprcWatcher("", "", 1)
        plugin.call = Mock()
        plugin.add_envs(name="name", envs={"foo": "bar"})
        plugin.call.assert_called_with("set",
                                       name="name",
                                       options={"env": {"foo": "bar"}})

    def test_look_after_add_envs(self):
        plugin = ApprcWatcher("", "", 1)
        plugin.call = Mock()
        plugin.call.return_value = {"statuses": {"name": "name", "cmd": "cmd"}}
        plugin.apprc = os.path.join(os.path.dirname(__file__),
                                    "testdata/apprc")
        plugin.look_after()
        env = {'VAR1': 'value-1', 'port': '8888', 'VAR2': 'value2'}
        plugin.call.assert_called_with("set",
                                       name="name",
                                       options={'env': env})
