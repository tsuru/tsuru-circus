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
        l = '2012-11-06 17:13:55 [12019] [INFO] Starting gunicorn 0.15.0\n'
        self.data = {
            'pid': 12018,
            'data': l,
            'name': 'stderr'
        }
        self.stream = Stream(watcher_name='mywatcher')
        self.stream.apprc = os.path.join(os.path.dirname(__file__),
                                         "testdata/apprc")

    def test_should_have_the_close_method(self):
        self.assertTrue(hasattr(Stream, "close"))

    @mock.patch("requests.post")
    def test_should_send_log_to_tsuru(self, post):
        post.return_value = mock.Mock(status_code=200)
        self.stream(self.data)
        appname, host, token = self.stream.load_envs()
        url = "{0}/apps/{1}/log?source=mywatcher".format(host, appname)
        expected_msg = "Starting gunicorn 0.15.0\n"
        expected_data = json.dumps([expected_msg])
        post.assert_called_with(url, data=expected_data,
                                headers={"Authorization": "bearer " + token})

    @mock.patch("tsuru.common.load_envs")
    def test_should_slience_errors_when_envs_does_not_exist(lenvs, self):
        lenvs.return_value = {}
        try:
            stream = Stream()
            stream(self.data)
        except Exception as e:
            msg = "Should not fail when envs does not exist. " \
                  "Exception: {}".format(e)
            self.fail(msg)
