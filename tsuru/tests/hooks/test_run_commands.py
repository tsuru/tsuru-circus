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
        self.watcher = Mock(name="somename", working_dir=working_dir,
                            uid="ubuntu")

    def cmd(self, command):
        cmd = "source /home/application/apprc && {}"
        return ["/bin/bash", "-c",
                cmd.format(command)]

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    @patch("tsuru.hooks.set_uid")
    def test_run_commands_with_config(self, set_uid,
                                      check_output, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh'],
            }
        }
        set_uid.return_value = 10
        run_commands('pre-restart', watcher=self.watcher)
        check_output.assert_called_with(self.cmd("testdata/pre.sh"),
                                        stderr=subprocess.STDOUT,
                                        cwd=self.watcher.working_dir,
                                        preexec_fn=10)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    @patch("tsuru.hooks.set_uid")
    def test_run_commands_colon_format(self, set_uid,
                                       check_output, load_config):
        load_config.return_value = {
            'hooks': {
                'restart': {
                    'before-each': ['testdata/pre.sh'],
                },
            },
        }
        set_uid.return_value = 10
        run_commands('restart:before-each', watcher=self.watcher)
        check_output.assert_called_with(self.cmd("testdata/pre.sh"),
                                        stderr=subprocess.STDOUT,
                                        cwd=self.watcher.working_dir,
                                        preexec_fn=10)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    @patch("tsuru.hooks.set_uid")
    def test_run_commands_without_config(self, set_uid, check_output,
                                         load_config):
        load_config.return_value = {
            'hooks': {'pre-restart': []}
        }
        run_commands('pre-restart', watcher=self.watcher)
        self.assertFalse(check_output.called)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    @patch("tsuru.hooks.set_uid")
    def test_run_commands_many_commands(self, set_uid,
                                        check_output, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh', 'testdata/pre2.sh'],
            }
        }
        set_uid.return_value = 10
        run_commands('pre-restart', watcher=self.watcher)
        calls = [call(self.cmd("testdata/pre.sh"), stderr=subprocess.STDOUT,
                      cwd=self.watcher.working_dir, preexec_fn=10),
                 call(self.cmd("testdata/pre2.sh"), stderr=subprocess.STDOUT,
                      cwd=self.watcher.working_dir, preexec_fn=10)]
        check_output.assert_has_calls(calls)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    @patch("tsuru.stream.Stream")
    @patch("tsuru.hooks.set_uid")
    def test_run_commands_should_log(self, set_uid, Stream,
                                     check_output, load_config):
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
    @patch("tsuru.hooks.set_uid")
    def test_should_return_true(self, set_uid, Stream, check_output,
                                load_config):
        result = run_commands('pre-restart', watcher=self.watcher)
        self.assertTrue(result)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    @patch("tsuru.stream.Stream")
    @patch("tsuru.hooks.set_uid")
    def test_run_commands_config_without_a_hook(self, set_uid, Stream,
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
    @patch("tsuru.hooks.set_uid")
    def test_run_commands_config_without_hooks(self, set_uid, Stream,
                                               check_output, load_config):
        load_config.return_value = {}
        run_commands('post-restart', watcher=self.watcher)

    @patch("tsuru.hooks.load_config")
    @patch("subprocess.check_output")
    @patch("tsuru.stream.Stream")
    @patch("tsuru.hooks.set_uid")
    def test_run_commands_that_returns_errors(self, set_uid, Stream,
                                              check_output, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['exit 1'],
            }
        }
        stream = Stream.return_value
        check_output.side_effect = subprocess.CalledProcessError(1, "cmd")
        run_commands('pre-restart', watcher=self.watcher)
        calls = [
            call({'data': ' ---> Running pre-restart'}),
            call({'data': "Command 'cmd' returned non-zero exit status 1"}),
            call({'data': None})
        ]
        stream.assert_has_calls(calls)

    @patch("tsuru.hooks.load_config")
    @patch("tsuru.stream.Stream")
    @patch("tsuru.hooks.set_uid")
    def test_log_only_when_commands_are_executed(self, set_uid,
                                                 Stream, load_config):
        load_config.return_value = {
            'hooks': {
                'pre-restart': ['ps -ef'],
            }
        }
        stream = Stream.return_value
        run_commands('post-restart', watcher=self.watcher)
        self.assertFalse(stream.called)
