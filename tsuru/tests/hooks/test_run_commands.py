# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import patch, call

from tsuru.hooks import run_commands


class RunCommandsTest(TestCase):
    @patch("tsuru.hooks.load_config")
    @patch("os.system")
    def test_run_commands_with_config(self, system, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh'],
            }
        }
        run_commands('pre-restart')
        system.assert_called_with("testdata/pre.sh")

    @patch("tsuru.hooks.load_config")
    @patch("os.system")
    def test_run_commands_without_config(self, system, load_config):
        load_config.return_value = {
            'hooks': {'pre-restart': [],}
        }
        run_commands('pre-restart')
        self.assertFalse(system.called)

    @patch("tsuru.hooks.load_config")
    @patch("os.system")
    def test_run_commands_many_commands(self, system, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh', 'testdata/pre2.sh'],
            }
        }
        run_commands('pre-restart')
        calls = [call("testdata/pre.sh"), call("testdata/pre2.sh")]
        system.assert_has_calls(calls)
