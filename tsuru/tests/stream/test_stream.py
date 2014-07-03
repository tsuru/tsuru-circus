# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import mock
import os
import json
import logging

from tsuru.stream import Stream


class StreamTestCase(unittest.TestCase):
    @mock.patch("tsuru.stream.gethostname")
    def setUp(self, gethostname):
        gethostname.return_value = "myhost"
        l_out = '2012-11-06 17:13:55 [12019] [INFO] Starting gunicorn 0.15.0\n'
        l_err = '2012-11-06 17:13:55 [12019] [ERROR] Error starting gunicorn\n'
        self.data = {}
        self.data['stderr'] = {
            'pid': 12018,
            'data': l_err,
            'name': 'stderr'
        }
        self.data['stdout'] = {
            'pid': 12018,
            'data': l_out,
            'name': 'stdout'
        }
        self.stream = Stream(watcher_name='mywatcher')
        self.stream.apprc = os.path.join(os.path.dirname(__file__),
                                         "testdata/apprc")

    def test_should_have_the_close_method(self):
        self.assertTrue(hasattr(Stream, "close"))

    @mock.patch("requests.post")
    def test_should_send_log_to_tsuru(self, post):
        post.return_value = mock.Mock(status_code=200)
        self.stream(self.data['stdout'])
        (appname, host, token, syslog_server,
         syslog_port, syslog_facility, syslog_socket) = self.stream.load_envs()
        url = "{0}/apps/{1}/log?source=mywatcher&unit=myhost".format(host,
                                                                     appname)
        expected_msg = "Starting gunicorn 0.15.0\n"
        expected_data = json.dumps([expected_msg])
        post.assert_called_with(url, data=expected_data,
                                headers={"Authorization": "bearer " + token},
                                timeout=2)

    @mock.patch("logging.getLogger")
    @mock.patch('logging.handlers.SysLogHandler')
    def test_should_send_log_to_syslog_as_info(self, s_handler, logger):
        self.stream(self.data['stdout'])
        (appname, host, token, syslog_server,
         syslog_port, syslog_facility, syslog_socket) = self.stream.load_envs()
        my_logger = logger(appname)
        log_handler = s_handler(address=(syslog_server, syslog_port),
                                facility=syslog_facility,
                                socktype=syslog_socket)
        expected_msg = "Starting gunicorn 0.15.0\n"
        my_logger.addHandler(log_handler)
        my_logger.info.assert_called_with(expected_msg)

    @mock.patch("logging.getLogger")
    @mock.patch('logging.handlers.SysLogHandler')
    def test_should_send_log_to_syslog_as_error(self, s_handler, logger):
        self.stream(self.data['stderr'])
        (appname, host, token, syslog_server,
         syslog_port, syslog_facility, syslog_socket) = self.stream.load_envs()
        my_logger = logger(appname)
        log_handler = s_handler(address=(syslog_server, syslog_port),
                                facility=syslog_facility,
                                socktype=syslog_socket)
        expected_msg = "Error starting gunicorn\n"
        my_logger.addHandler(log_handler)
        my_logger.error.assert_called_with(expected_msg)

    def test_should_send_log_to_syslog_and_use_one_handler(self):
        self.stream(self.data['stderr'])
        self.stream(self.data['stderr'])
        self.stream(self.data['stderr'])
        self.stream(self.data['stderr'])
        (appname, host, token, syslog_server,
         syslog_port, syslog_facility, syslog_socket) = self.stream.load_envs()
        my_logger = logging.getLogger(appname)
        self.assertEqual(len(my_logger.handlers), 1)

    @mock.patch("tsuru.stream.gethostname")
    @mock.patch("requests.post")
    def test_timeout_is_configurable(self, post, gethostname):
        post.return_value = mock.Mock(status_code=200)
        gethostname.return_value = "myhost"
        stream = Stream(watcher_name="watcher", timeout=10)
        stream.apprc = os.path.join(os.path.dirname(__file__),
                                    "testdata/apprc")
        stream(self.data['stdout'])
        (appname, host, token, syslog_server,
         syslog_port, syslog_facility, syslog_socket) = self.stream.load_envs()
        url = "{0}/apps/{1}/log?source=watcher&unit=myhost".format(host,
                                                                   appname)
        expected_msg = "Starting gunicorn 0.15.0\n"
        expected_data = json.dumps([expected_msg])
        post.assert_called_with(url, data=expected_data,
                                headers={"Authorization": "bearer " + token},
                                timeout=10)

    @mock.patch("requests.post")
    def test_should_ignore_errors_in_post_call(self, post):
        post.side_effect = Exception()
        self.stream(self.data['stdout'])

    @mock.patch("tsuru.common.load_envs")
    def test_should_slience_errors_when_envs_does_not_exist(lenvs, self):
        lenvs.return_value = {}
        try:
            stream = Stream()
            stream(self.data['stdout'])
        except Exception as e:
            msg = "Should not fail when envs does not exist. " \
                  "Exception: {}".format(e)
            self.fail(msg)

    def test_get_messagess_no_buffering(self):
        stream = Stream()
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
            "Exception in worker process:\n",
            "Traceback (most recent call last):\n",
        ]
        messages = stream.get_messages(msg)
        self.assertEqual("", stream._buffer)
        self.assertEqual(expected, messages)

    def test_get_messagess_buffering(self):
        stream = Stream()
        msg = "2012-11-06 18:30:10 [13887] [INFO] Listening at: " \
              "http://127.0.0.1:8000 (13887)\n2012-11-06 18:30:10 [13887] " \
              "[INFO] Using worker: sync\n2012-11-06 18:30:10 [13890] " \
              "[INFO] Booting worker with pid: 13890\n2012-11-06 18:30:10 " \
              "[13890] [ERROR] Exception in worker process:\nTraceback " \
              "(most recent call last):"
        expected = [
            "Listening at: http://127.0.0.1:8000 (13887)\n",
            "Using worker: sync\n",
            "Booting worker with pid: 13890\n",
            "Exception in worker process:\n",
        ]
        messages = stream.get_messages(msg)
        self.assertEqual("Traceback (most recent call last):", stream._buffer)
        self.assertEqual(expected, messages)

    def test_get_messagess_buffered(self):
        stream = Stream()
        msg1 = "2012-11-06 18:30:10 [13887] [INFO] Listening at: " \
               "http://127.0.0.1:8000 (13887)\n2012-11-06 18:30:10 [13887] "
        msg2 = "[INFO] Using worker: sync\n2012-11-06 18:30:10 "
        msg3 = "[13890] [INFO] Booting worker with pid: 13890\n2012-11-06 " \
               "18:30:10 [13890] [ERROR] Exception in worker process:\n" \
               "Traceback (most recent call last):\n"
        expected = [
            "Listening at: http://127.0.0.1:8000 (13887)\n",
            "Using worker: sync\n",
            "Booting worker with pid: 13890\n",
            "Exception in worker process:\n",
            "Traceback (most recent call last):\n",
        ]
        self.assertEqual(expected[:1], stream.get_messages(msg1))
        self.assertEqual(expected[1:2], stream.get_messages(msg2))
        self.assertEqual(expected[2:], stream.get_messages(msg3))

    def test_get_messagess_full_buffer(self):
        stream = Stream()
        stream._max_buffer_size = 20
        stream._buffer = 13 * "a"
        msg = "2012-11-06 18:30:10 [13887] [INFO] Listening at: " \
              "http://127.0.0.1:8000 (13887)"
        expected = [stream._buffer +
                    "Listening at: http://127.0.0.1:8000 (13887)"]
        self.assertEqual(expected, stream.get_messages(msg))

    def test_get_messages_buffered_multiple_times(self):
        stream = Stream()
        msg1 = "2012-11-06 18:30:10 [13887] [INFO] Listening at: " \
               "http://127.0.0.1:8000 (13887)\n2012-11-06 18:30:10 [13887] "
        msg2 = "[INFO] Using worker: sync\n2012-11-06 18:30:10 "
        msg3 = "[13890] [INFO] Booting worker with pid: 13890\n2012-11-06 " \
               "18:30:10 [13890] [ERROR] Exception in worker process:\n" \
               "Traceback (most recent call last):"
        msg4 = "\n2012-11-06 18:30:10 [13887] [INFO] Booting another worker "\
               "with pid: 13891\n"
        expected = [
            "Listening at: http://127.0.0.1:8000 (13887)\n",
            "Using worker: sync\n",
            "Booting worker with pid: 13890\n",
            "Exception in worker process:\n",
            "Traceback (most recent call last):\n",
            "Booting another worker with pid: 13891\n",
        ]
        self.assertEqual(expected[:1], stream.get_messages(msg1))
        self.assertEqual(expected[1:2], stream.get_messages(msg2))
        self.assertEqual(expected[2:4], stream.get_messages(msg3))
        self.assertEqual(expected[4:], stream.get_messages(msg4))

    def test_get_messages_sequential_bufferings(self):
        stream = Stream()
        msg1 = "2012-11-06 18:30:10 [13887] [INFO] Listening at: "
        msg2 = "http://127.0.0.1:8000 "
        msg3 = "(13887)\n"
        self.assertEqual([], stream.get_messages(msg1))
        self.assertEqual([], stream.get_messages(msg2))
        self.assertEqual(["Listening at: http://127.0.0.1:8000 (13887)\n"],
                         stream.get_messages(msg3))

    def test_default_max_buffer_size(self):
        stream = Stream()
        self.assertEqual(10240, stream._max_buffer_size)

    def test_max_buffer_size_is_configurable(self):
        stream = Stream(max_buffer_size=500)
        self.assertEqual(500, stream._max_buffer_size)
