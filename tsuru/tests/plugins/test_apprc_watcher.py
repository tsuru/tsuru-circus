# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import Mock
from tsuru.plugins import ApprcWatcher


class ApprcWatcherTest(TestCase):
    def test_add_envs(self):
        plugin = ApprcWatcher("", "", 1)
        plugin.call = Mock()
        plugin.add_envs(name="name", envs={"foo": "bar"})
        plugin.call.assert_called_with("set", name="name", options={"env": {"foo": "bar"}})
