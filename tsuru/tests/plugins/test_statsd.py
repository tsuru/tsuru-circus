import os

from tornado.testing import gen_test

from circus.tests.support import TestCircus, async_poll_for
from circus.tests.support import async_run_plugin

from tsuru.plugins.statsd import Stats, StatsdEmitter

from mock import patch


def get_gauges(queue, plugin):
    queue.put(plugin.statsd.gauges)


class TestStats(TestCircus):

    @gen_test
    def test_stats(self):
        dummy_process = 'circus.tests.support.run_process'
        yield self.start_arbiter(dummy_process)
        async_poll_for(self.test_file, 'START')

        config = {'loop_rate': 0.2}
        gauges = yield async_run_plugin(
            Stats, config,
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

    @patch("circus.plugins.statsd.StatsdClient")
    def test_prefix(self, client_mock):
        os.environ["HOSTNAME"] = "somehost"
        os.environ["TSURU_APPNAME"] = "appname"
        StatsdEmitter("endpoint", "pubsub", 1.0, "ssh_server")
        client_mock.assert_called_with(host='localhost', sample_rate=1.0,
                                       prefix='tsuru.appname.somehost',
                                       port=8125)

    @patch("circus.plugins.statsd.StatsdClient")
    def test_statsd_host(self, client_mock):
        os.environ["STATSD_HOST"] = "statsdhost"
        os.environ["STATSD_PORT"] = "21"
        StatsdEmitter("endpoint", "pubsub", 1.0, "ssh_server")
        client_mock.assert_called_with(host='statsdhost', sample_rate=1.0,
                                       prefix='tsuru.appname.somehost',
                                       port=21)

        del os.environ["STATSD_HOST"]
        del os.environ["STATSD_PORT"]
        StatsdEmitter("endpoint", "pubsub", 1.0, "ssh_server")
        client_mock.assert_called_with(host='localhost', sample_rate=1.0,
                                       prefix='tsuru.appname.somehost',
                                       port=8125)
