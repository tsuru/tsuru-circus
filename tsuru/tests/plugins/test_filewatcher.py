# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import unittest

from tsuru.plugins import FileWatcher


class FileWatcherTest(unittest.TestCase):

    def test_invokes_callback(self):
        calls = {"callback": 0}

        def callback():
            calls["callback"] += 1

        path = os.path.join(os.path.dirname(__file__),
                            "testdata/apprc")
        watcher = FileWatcher(path, callback)
        watcher()
        self.assertEqual(1, calls["callback"])
        watcher()
        self.assertEqual(1, calls["callback"])
        os.system("touch %s" % path)
        watcher()
        self.assertEqual(2, calls["callback"])
