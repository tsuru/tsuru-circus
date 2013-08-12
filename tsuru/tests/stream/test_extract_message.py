# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest

from tsuru.stream import extract_message


class ExtractMessageTestCase(unittest.TestCase):
    def test_extract_message_when_it_isnt_a_list(self):
        msg = 'Starting gunicorn 0.15.0'
        expected = 'Starting gunicorn 0.15.0'
        result = extract_message(msg)
        self.assertListEqual([expected], result)

    def test_extract_message(self):
        msg = '2012-11-06 17:13:55 [12019] [INFO] Starting gunicorn 0.15.0'
        expected = 'Starting gunicorn 0.15.0'
        result = extract_message(msg)
        self.assertListEqual([expected], result)

    def test_extract_multiline(self):
        msg = "2012-11-06 18:30:10 [13887] [INFO] Listening at: " \
              "http://127.0.0.1:8000 (13887)\n2012-11-06 18:30:10 [13887] " \
              "[INFO] Using worker: sync\n2012-11-06 18:30:10 [13890] " \
              "[INFO] Booting worker with pid: 13890\n2012-11-06 18:30:10 " \
              "[13890] [ERROR] Exception in worker process:\nTraceback " \
              "(most recent call last):\n"
        expected = [
            "Listening at: http://127.0.0.1:8000 (13887)\n",
            "Using worker: sync\n",
            "Booting worker with pid: 13890\n",
            "Exception in worker process:\nTraceback "
            "(most recent call last):\n",
        ]
        result = extract_message(msg)
        self.assertListEqual(expected, result)
