# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import patch, call

from tsuru.hooks import after_start


class AfterStartTest(TestCase):
    @patch("tsuru.hooks.load_config")
    @patch("os.system")
    def test_after_start(self, system, load_config):
        load_config.return_value = {
            'post-restart': ['testdata/post.sh'],
        }
        after_start()
        system.assert_called_with("testdata/post.sh")

    @patch("tsuru.hooks.load_config")
    @patch("os.system")
    def test_after_start_many_commands(self, system, load_config):
        load_config.return_value = {
            'post-restart': ['testdata/post.sh', 'testdata/post2.sh'],
        }
        after_start()
        calls = [call("testdata/post.sh"), call("testdata/post2.sh")]
        system.assert_has_calls(calls)
