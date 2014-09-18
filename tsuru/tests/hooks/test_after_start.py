# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase

from tsuru.hooks import after_start


class AfterStartTest(TestCase):
    def test_after_start(self):
        result = after_start()
        self.assertTrue(result)
