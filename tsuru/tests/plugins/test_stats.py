# Copyright 2015 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from tornado.testing import gen_test
from circus.tests.support import TestCircus, async_poll_for
from circus.util import DEFAULT_ENDPOINT_DEALER, DEFAULT_ENDPOINT_SUB
from circus.util import tornado_sleep
from tsuru.plugins.statsd import Stats, storages
from tsuru.plugins.stats.fake import FakeBackend
from tsuru.plugins.stats.statsd import StatsdBackend
from tsuru.plugins.stats.logstash import LogstashBackend
from mock import patch, Mock
import tornado

from time import time
import multiprocessing
import functools
import os


def run_plugin(cls, config, plugin_info_callback=None, duration=300,
               endpoint=DEFAULT_ENDPOINT_DEALER, pubsub_endpoint=DEFAULT_ENDPOINT_SUB):
    check_delay = 1
    ssh_server = None

    plugin = cls(endpoint, pubsub_endpoint, check_delay, ssh_server, **config)

    if hasattr(plugin, 'storage'):
        plugin.storage.stop()

    deadline = time() + (duration / 1000.)
    plugin.loop.add_timeout(deadline, plugin.stop)

    plugin.start()
    try:
        if plugin_info_callback:
            plugin_info_callback(plugin)
    finally:
        plugin.stop()

    return plugin.storage


@tornado.gen.coroutine
def async_run_plugin(cls, config, plugin_info_callback, duration=300,
                     endpoint=DEFAULT_ENDPOINT_DEALER, pubsub_endpoint=DEFAULT_ENDPOINT_SUB):
    queue = multiprocessing.Queue()
    plugin_info_callback = functools.partial(plugin_info_callback, queue)
    circusctl_process = multiprocessing.Process(
        target=run_plugin,
        args=(cls, config, plugin_info_callback, duration, endpoint, pubsub_endpoint))
    circusctl_process.start()

    while queue.empty():
        yield tornado_sleep(.1)

    result = queue.get()
    raise tornado.gen.Return(result)


def get_gauges(queue, plugin):
    queue.put(plugin.storage.gauges)


class TestStats(TestCircus):

    @gen_test
    def test_stats(self):
        envs = {
            "TSURU_METRICS_BACKEND": "fake",
        }
        os.environ.update(envs)
        dummy_process = 'circus.tests.support.run_process'
        yield self.start_arbiter(dummy_process)
        async_poll_for(self.test_file, 'START')

        config = {'loop_rate': 0.2}
        stats_class = Stats
        stats_class.disk_usage = lambda x: 0
        stats_class.net_io = lambda x: (0, 0)
        stats_class.connections_established = lambda x: 0
        stats_class.connections = lambda x: []
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

    def test_get_storage(self):
        envs = {
            "TSURU_METRICS_BACKEND": "fake",
        }
        os.environ.update(envs)
        stats = Stats("endpoint", "pubsub", 1.0, "ssh_server")
        storage = stats.get_storage()
        self.assertIsInstance(storage, FakeBackend)

    def test_statsd_default_storage(self):
        del os.environ["TSURU_METRICS_BACKEND"]
        stats = Stats("endpoint", "pubsub", 1.0, "ssh_server")
        storage = stats.get_storage()
        self.assertIsInstance(storage, StatsdBackend)

    def test_logstash_registered(self):
        self.assertIn("logstash", storages)
        self.assertIsInstance(storages["logstash"](), LogstashBackend)

    def test_get_a_not_registered_backend(self):
        envs = {
            "TSURU_METRICS_BACKEND": "doesnotexist",
        }
        os.environ.update(envs)
        stats = Stats("endpoint", "pubsub", 1.0, "ssh_server")
        storage = stats.get_storage()
        # when a backend does not exists the default should be returned
        self.assertIsInstance(storage, StatsdBackend)
