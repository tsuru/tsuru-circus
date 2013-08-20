# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import patch

from tsuru.hooks import after_start


class AfterStartTest(TestCase):
    @patch("tsuru.hooks.run_commands")
    def test_after_start(self, run_commands):
        run_commands.return_value = True
        result = after_start()
        run_commands.assert_called_with('post-restart')
        self.assertTrue(result)
