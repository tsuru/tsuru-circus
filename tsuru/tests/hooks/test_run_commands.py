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
            'pre-restart': ['testdata/pre.sh'],
        }
        run_commands('pre-restart')
        system.assert_called_with("testdata/pre.sh")
