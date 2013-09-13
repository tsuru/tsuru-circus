# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import call, patch

from tsuru.hooks import before_start


class BeforeStartTest(TestCase):
    @patch("tsuru.hooks.run_commands")
    def test_before_start(self, run_commands):
        run_commands.return_value = True
        result = before_start()
        calls = [call('restart:before-each'),
                 call('pre-restart')]
        run_commands.assert_has_calls(calls)
        self.assertTrue(result)
