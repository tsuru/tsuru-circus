# Copyright 2015 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
import os

from tsuru.plugins.stats.statsd import StatsdBackend
from mock import patch, Mock


class TestStatsd(TestCase):

    @patch("socket.gethostname")
    @patch("circus.plugins.statsd.StatsdClient")
    def setUp(self, statsd_client_mock, gethostname_mock):
        gethostname_mock.return_value = "somehost"
        envs = {
            "TSURU_APPNAME": "appname",
        }
        os.environ.update(envs)
        self.statsd = StatsdBackend()
        self.statsd.gauge = Mock()
        statsd_client_mock.assert_called_with(
            host='localhost', sample_rate=1.0, prefix='tsuru.appname.somehost', port=8125)

    def test_mem_max(self):
        self.statsd.mem_max("name", 123)
        self.statsd.gauge.assert_called_with('name.mem_max', 123)

    def test_cpu_max(self):
        self.statsd.cpu_max("name", 123)
        self.statsd.gauge.assert_called_with('name.cpu_max', 123)

    def test_mem_sum(self):
        self.statsd.mem_sum("name", 123)
        self.statsd.gauge.assert_called_with('name.mem_sum', 123)

    def test_cpu_sum(self):
        self.statsd.cpu_sum("name", 123)
        self.statsd.gauge.assert_called_with('name.cpu_sum', 123)

    def test_mem_pct_sum(self):
        self.statsd.mem_pct_sum("name", 123)
        self.statsd.gauge.assert_called_with('name.mem_pct_sum', 123)

    def test_mem_pct_max(self):
        self.statsd.mem_pct_max("name", 123)
        self.statsd.gauge.assert_called_with('name.mem_pct_max', 123)

    def test_disk_usage(self):
        self.statsd.disk_usage(123)
        self.statsd.gauge.assert_called_with('disk_usage', 123)

    def test_net_sent(self):
        self.statsd.net_sent(123)
        self.statsd.gauge.assert_called_with('net.sent', 123)

    def test_net_recv(self):
        self.statsd.net_recv(123)
        self.statsd.gauge.assert_called_with('net.recv', 123)

    def test_net_connections(self):
        self.statsd.net_connections(123)
        self.statsd.gauge.assert_called_with('net.connections', 123)

    @patch("socket.gethostname")
    def test_gauge(self, gethostname_mock):
        gethostname_mock.return_value = "somehost"
        envs = {
            "TSURU_APPNAME": "appname",
        }
        os.environ.update(envs)
        statsd = StatsdBackend()
        statsd.client = Mock()

        statsd.gauge("key", "value")

        statsd.client.gauge.assert_called_with("key", "value")
