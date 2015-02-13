# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from tornado.testing import gen_test

from circus.tests.support import TestCircus, async_poll_for
from circus.tests.support import async_run_plugin

from tsuru.plugins.statsd import Stats, StatsdEmitter

from mock import patch, Mock

import os


def get_gauges(queue, plugin):
    queue.put(plugin.statsd.gauges)


class TestStats(TestCircus):

    @gen_test
    def test_stats(self):
        dummy_process = 'circus.tests.support.run_process'
        yield self.start_arbiter(dummy_process)
        async_poll_for(self.test_file, 'START')

        config = {'loop_rate': 0.2}
        stats_class = Stats
        stats_class.disk_usage = lambda x: 0
        stats_class.net_io = lambda x: (0, 0)
        stats_class.connections_established = lambda x: 0
        gauges = yield async_run_plugin(
            stats_class, config,
            plugin_info_callback=get_gauges,
            duration=1000,
            endpoint=self.arbiter.endpoint,
            pubsub_endpoint=self.arbiter.pubsub_endpoint
        )

        # we should have a bunch of stats events here
        self.assertTrue(len(gauges) >= 5)
        last_batch = sorted(name for name, value in gauges[-5:])
        wanted = ['test.cpu_sum', 'test.mem_max',
                  'test.mem_pct_max', 'test.mem_pct_sum',
                  'test.mem_sum']
        self.assertEqual(last_batch, wanted)

        yield self.stop_arbiter()

    @patch("socket.gethostname")
    @patch("circus.plugins.statsd.StatsdClient")
    def test_prefix(self, client_mock, gethostname_mock):
        gethostname_mock.return_value = "somehost"
        envs = {
            "TSURU_APPNAME": "appname",
        }
        os.environ.update(envs)
        StatsdEmitter("endpoint", "pubsub", 1.0, "ssh_server")
        client_mock.assert_called_with(host='localhost', sample_rate=1.0,
                                       prefix='tsuru.appname.somehost',
                                       port=8125)

    @patch("socket.gethostname")
    @patch("circus.plugins.statsd.StatsdClient")
    def test_statsd_host(self, client_mock, gethostname_mock):
        gethostname_mock.return_value = "somehost"
        envs = {
            "STATSD_HOST": "statsdhost",
            "STATSD_PORT": "21",
            "TSURU_APPNAME": "appname",
        }
        os.environ.update(envs)
        StatsdEmitter("endpoint", "pubsub", 1.0, "ssh_server")
        client_mock.assert_called_with(host='statsdhost', sample_rate=1.0,
                                       prefix='tsuru.appname.somehost',
                                       port=21)
        envs = {
            "TSURU_APPNAME": "appname",
            "STATSD_HOST": "",
            "STATSD_PORT": "",
        }
        os.environ.update(envs)
        StatsdEmitter("endpoint", "pubsub", 1.0, "ssh_server")
        client_mock.assert_called_with(host='localhost', sample_rate=1.0,
                                       prefix='tsuru.appname.somehost',
                                       port=8125)

    @patch("psutil.disk_usage")
    def test_disk_usage(self, disk_usage_mock):
        stats = Stats("endpoint", "pubsub", 1.0, "ssh_server")
        stats.disk_usage()

        disk_usage_mock.assert_called_with("/")

    @patch("psutil.net_io_counters")
    def test_net_io(self, net_io_mock):
        stats = Stats("endpoint", "pubsub", 1.0, "ssh_server")
        stats.net_io()

        net_io_mock.assert_called_with()

    @patch("psutil.net_connections")
    def test_connections_established(self, conn_mock):
        conn = Mock(status="ESTABLISHED")
        conn_mock.return_value = [conn, conn, conn, conn, conn]

        stats = Stats("endpoint", "pubsub", 1.0, "ssh_server")
        established = stats.connections_established()

        self.assertEqual(5, established)

        conn_mock.assert_called_with("tcp")
