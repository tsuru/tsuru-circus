# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import patch

from tsuru.hooks import before_start


class BeforeStartTest(TestCase):
    @patch("tsuru.hooks.run_commands")
    def test_before_start(self, run_commands):
        run_commands.return_value = True
        result = before_start()
        run_commands.assert_called_with('pre-restart')
        self.assertTrue(result)
