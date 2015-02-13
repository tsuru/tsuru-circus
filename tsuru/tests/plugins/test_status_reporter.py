# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import socket
import unittest
import mock
import os

from tsuru.plugins import StatusReporter


class StatusReporterTestCase(unittest.TestCase):

    def test_init(self):
        hostname = socket.gethostname()
        status_reporter = StatusReporter("", "", 1,
                                         loop_rate="180",
                                         apprc="/etc/apprc")
        self.assertEqual(180, status_reporter.loop_rate)
        self.assertEqual(hostname, status_reporter.hostname)

    def test_init_default_config_values(self):
        status_reporter = StatusReporter("", "", 1)
        self.assertEqual(60, status_reporter.loop_rate)

    def test_handle_init(self):
        status_reporter = StatusReporter("", "", 1)
        status_reporter.period.start = mock.Mock()
        status_reporter.handle_init()
        status_reporter.period.start.assert_called_once()

    def test_handle_stop(self):
        status_reporter = StatusReporter("", "", 1)
        status_reporter.period.stop = mock.Mock()
        status_reporter.handle_stop()
        status_reporter.period.stop.assert_called_once()

    @mock.patch("requests.post")
    @mock.patch("tsuru.plugins.gethostname")
    def test_report_ignores_plugins(self, gethostname, post):
        gethostname.return_value = "myhost"
        status_reporter = StatusReporter("", "", 1)
        envs = {
            "TSURU_HOST": "http://tsuru.io:8080",
            "TSURU_APP_TOKEN": "abc123",
            "TSURU_APPNAME": "something"
        }
        os.environ.update(envs)
        call = mock.Mock()
        call.return_value = {"statuses": {"plugin:tsuru-hooks": "stopped",
                                          "something": "active"}}
        status_reporter.call = call
        status_reporter.report()
        call.assert_called_once()
        url = "http://tsuru.io:8080/apps/something/units/myhost"
        post.assert_called_with(url, data={"status": "started"},
                                headers={"Authorization": "bearer abc123"})

    @mock.patch("requests.post")
    @mock.patch("tsuru.plugins.gethostname")
    def test_report_non_active_process(self, gethostname, post):
        gethostname.return_value = "myhost"
        status_reporter = StatusReporter("", "", 1)
        envs = {
            "TSURU_HOST": "http://tsuru.io:8080",
            "TSURU_APP_TOKEN": "abc123",
            "TSURU_APPNAME": "something"
        }
        os.environ.update(envs)
        call = mock.Mock()
        call.return_value = {"statuses": {"otherthing": "active",
                                          "something": "active",
                                          "wat": "stopped"}}
        status_reporter.call = call
        status_reporter.report()
        call.assert_called_once()
        url = "http://tsuru.io:8080/apps/something/units/myhost"
        post.assert_called_with(url, data={"status": "error"},
                                headers={"Authorization": "bearer abc123"})
