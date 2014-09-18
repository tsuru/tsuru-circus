# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase

from tsuru.hooks import before_start


class BeforeStartTest(TestCase):
    def test_before_start(self):
        result = before_start()
        self.assertTrue(result)
