# Copyright 2015 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
import os

from tsuru.plugins.stats.logstash import LogstashBackend
from mock import patch, Mock


class TestLogstash(TestCase):

    @patch("socket.gethostname")
    def setUp(self, gethostname_mock):
        gethostname_mock.return_value = "somehost"
        envs = {
            "TSURU_APPNAME": "appname",
        }
        os.environ.update(envs)
        self.logstash = LogstashBackend()
        self.logstash.gauge = Mock()

    def test_init(self):
        self.assertEqual(self.logstash.app_name, "appname")
        self.assertEqual(self.logstash.host_name, "somehost")

    def test_mem_max(self):
        self.logstash.mem_max("name", 123)
        self.logstash.gauge.assert_called_with('mem_max', 123)

    def test_cpu_max(self):
        self.logstash.cpu_max("name", 123)
        self.logstash.gauge.assert_called_with('cpu_max', 123)

    def test_mem_sum(self):
        self.logstash.mem_sum("name", 123)
        self.logstash.gauge.assert_called_with('mem_sum', 123)

    def test_cpu_sum(self):
        self.logstash.cpu_sum("name", 123)
        self.logstash.gauge.assert_called_with('cpu_sum', 123)

    def test_mem_pct_sum(self):
        self.logstash.mem_pct_sum("name", 123)
        self.logstash.gauge.assert_called_with('mem_pct_sum', 123)

    def test_mem_pct_max(self):
        self.logstash.mem_pct_max("name", 123)
        self.logstash.gauge.assert_called_with('mem_pct_max', 123)

    def test_disk_usage(self):
        self.logstash.disk_usage(123)
        self.logstash.gauge.assert_called_with('disk_usage', 123)

    def test_net_sent(self):
        self.logstash.net_sent(123)
        self.logstash.gauge.assert_called_with('net_sent', 123)

    def test_net_recv(self):
        self.logstash.net_recv(123)
        self.logstash.gauge.assert_called_with('net_recv', 123)

    def test_net_connections(self):
        self.logstash.net_connections(123)
        self.logstash.gauge.assert_called_with('net_connections', 123)

    @patch("socket.gethostname")
    def test_gauge(self, gethostname_mock):
        gethostname_mock.return_value = "somehost"
        envs = {
            "TSURU_APPNAME": "appname",
        }
        os.environ.update(envs)
        logstash = LogstashBackend()
        logstash.measure = Mock()

        logstash.gauge("key", "value")

        dimensions = {'app': 'appname', 'host': 'somehost', 'value': 'value'}
        logstash.measure.count.assert_called_with('key', dimensions=dimensions)
