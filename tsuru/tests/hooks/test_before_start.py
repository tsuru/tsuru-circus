# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import patch, call

from tsuru.hooks import before_start


class BeforeStartTest(TestCase):
    @patch("tsuru.hooks.load_config")
    @patch("os.system")
    def test_before_start(self, system, load_config):
        load_config.return_value = {
            'pre-restart': ['testdata/pre.sh'],
        }
        before_start()
        system.assert_called_with("testdata/pre.sh")

    @patch("tsuru.hooks.load_config")
    @patch("os.system")
    def test_before_start_many_commands(self, system, load_config):
        load_config.return_value = {
            'pre-restart': ['testdata/pre.sh', 'testdata/pre2.sh'],
        }
        before_start()
        calls = [call("testdata/pre.sh"), call("testdata/pre2.sh")]
        system.assert_has_calls(calls)
