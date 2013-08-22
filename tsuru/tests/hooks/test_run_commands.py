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

    def cmd(self, command):
        source = "source /home/application/apprc &&"
        return "{} cd {} && {}".format(source, self.watcher.working_dir,
                                       command)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    def test_run_commands_with_config(self, check_output, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh'],
            }
        }
        run_commands('pre-restart', watcher=self.watcher)
        check_output.assert_called_with([self.cmd("testdata/pre.sh")],
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
        calls = [call([self.cmd("testdata/pre.sh")], stderr=subprocess.STDOUT,
                      shell=True),
                 call([self.cmd("testdata/pre2.sh")], stderr=subprocess.STDOUT,
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

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    @patch("tsuru.stream.Stream")
    def test_should_return_true(self, Stream, check_output, load_config):
        result = run_commands('pre-restart', watcher=self.watcher)
        self.assertTrue(result)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    @patch("tsuru.stream.Stream")
    def test_run_commands_config_without_a_hook(self, Stream,
                                                check_output, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh'],
            }
        }
        run_commands('post-restart', watcher=self.watcher)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    @patch("tsuru.stream.Stream")
    def test_run_commands_config_without_hooks(self, Stream,
                                               check_output, load_config):
        load_config.return_value = {}
        run_commands('post-restart', watcher=self.watcher)

    @patch("tsuru.hooks.load_config")
    @patch("tsuru.stream.Stream")
    def test_run_commands_that_returns_errors(self, Stream, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['exit 1'],
            }
        }
        stream = Stream.return_value
        run_commands('pre-restart', watcher=self.watcher)
        cmd = self.cmd('exit 1')
        calls = [
            call({"data": " ---> Running pre-restart"}),
            call({'data':
                  "Command '['{}']' returned non-zero exit status 1".format(
                      cmd)})
        ]
        stream.assert_has_calls(calls)

    @patch("tsuru.hooks.load_config")
    @patch("tsuru.stream.Stream")
    def test_log_only_when_the_commands_is_executed(self, Stream, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['ps -ef'],
            }
        }
        stream = Stream.return_value
        run_commands('post-restart', watcher=self.watcher)
        self.assertFalse(stream.called)
