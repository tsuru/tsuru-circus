# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import patch, call, Mock
import os
import subprocess

from tsuru.hooks import run_commands


class RunCommandsTest(TestCase):
    def setUp(self):
        working_dir = os.path.dirname(__file__)
        self.watcher = Mock(name="somename", working_dir=working_dir)
        self.cd = "cd {}".format(working_dir)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    def test_run_commands_with_config(self, check_output, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh'],
            }
        }
        run_commands('pre-restart', watcher=self.watcher)
        check_output.assert_called_with([self.cd, "testdata/pre.sh"],
                                        stderr=subprocess.STDOUT, shell=True)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    def test_run_commands_without_config(self, check_output, load_config):
        load_config.return_value = {
            'hooks': {'pre-restart': []}
        }
        run_commands('pre-restart', watcher=self.watcher)
        self.assertFalse(check_output.called)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    def test_run_commands_many_commands(self, check_output, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh', 'testdata/pre2.sh'],
            }
        }
        run_commands('pre-restart', watcher=self.watcher)
        calls = [call([self.cd, "testdata/pre.sh"], stderr=subprocess.STDOUT,
                      shell=True),
                 call([self.cd, "testdata/pre2.sh"], stderr=subprocess.STDOUT,
                      shell=True)]
        check_output.assert_has_calls(calls)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    @patch("tsuru.stream.Stream")
    def test_run_commands_should_log(self, Stream, check_output, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh'],
            }
        }
        check_output.return_value = "ble"
        stream = Stream.return_value
        run_commands('pre-restart', watcher=self.watcher)
        calls = [call({"data": " ---> Running pre-restart"}),
                 call({"data": "ble"})]
        stream.assert_has_calls(calls)
