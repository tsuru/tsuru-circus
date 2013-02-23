# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import mock
import os
import json

from tsuru.stream import Stream


class StreamTestCase(unittest.TestCase):
    def setUp(self):
        self.data = {
            'pid': 12018,
            'data': '2012-11-06 17:13:55 [12019] [INFO] Starting gunicorn 0.15.0\n',
            'name': 'stderr'
        }
        self.stream = Stream(tsuru_host="http://someurl.com", tsuru_appname="myapp")

    def test_should_have_the_close_method(self):
        self.assertTrue(hasattr(Stream, "close"))

    @mock.patch("requests.post")
    def test_should_send_log_to_tsuru(self, post):
            post.return_value = mock.Mock(status_code=200)
            self.stream(self.data)
            url = "{0}/apps/{1}/log".format(self.stream.tsuru_host, self.stream.tsuru_appname)
            expected_msg = "Starting gunicorn 0.15.0\n"
            expected_data = json.dumps([expected_msg,])
            post.assert_called_with(url, data=expected_data)

    def test_should_slience_errors_when_envs_does_not_exist(self):
        try:
            Stream()(self.data)
        except:
            assert False
