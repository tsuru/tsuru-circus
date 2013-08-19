# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import patch, call

from tsuru.hooks import run_commands


class RunCommandsTest(TestCase):
    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    def test_run_commands_with_config(self, check_output, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh'],
            }
        }
        run_commands('pre-restart')
        check_output.assert_called_with(["testdata/pre.sh"], shell=True)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    def test_run_commands_without_config(self, check_output, load_config):
        load_config.return_value = {
            'hooks': {'pre-restart': []}
        }
        run_commands('pre-restart')
        self.assertFalse(check_output.called)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    def test_run_commands_many_commands(self, check_output, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh', 'testdata/pre2.sh'],
            }
        }
        run_commands('pre-restart')
        calls = [call(["testdata/pre.sh"], shell=True),
                 call(["testdata/pre2.sh"], shell=True)]
        check_output.assert_has_calls(calls)
