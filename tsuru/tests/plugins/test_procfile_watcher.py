# Copyright 2015 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase

from tsuru.plugins import ProcfileWatcher


class ProcfileWatcherTest(TestCase):
    def test_plugin(self):
        plugin = ProcfileWatcher("", "", 1)
        self.assertIsInstance(plugin, ProcfileWatcher)
