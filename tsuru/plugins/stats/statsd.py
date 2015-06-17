# Copyright 2015 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import socket


class StatsdBackend(object):

    def __init__(self):
        envs = os.environ

        app_name = envs.get("TSURU_APPNAME")
        host_name = socket.gethostname()

        # initialize statsd
        from circus.plugins.statsd import StatsdClient
        host = envs.get("STATSD_HOST", 'localhost') or "localhost"
        port = envs.get("STATSD_PORT", '8125') or "8125"
        namespace = envs.get("STATSD_PREFIX", '') or ""

        if namespace != "":
            statsd_prefix = "{}.".format(namespace)
        else:
            statsd_prefix = ""

        # tsuru.app.host
        self.prefix = '{}tsuru.{}.{}'.format(
            statsd_prefix, app_name, host_name)

        self.client = StatsdClient(
            host=host,
            port=int(port),
            prefix=self.prefix,
            sample_rate=1.0
        )

    def stop(self):
        self.client.stop()

    def gauge(self, key, value):
        self.client.gauge(key, value)

    def disk_usage(self, value):
        self.gauge("disk_usage", value)

    def net_sent(self, value):
        self.gauge("net.sent", value)

    def net_recv(self, value):
        self.gauge("net.recv", value)

    def net_connections(self, value):
        self.gauge("net.connections", value)

    def connections(self, value):
        pass

    def cpu_max(self, name, value):
        self.gauge("{}.cpu_max".format(name), value)

    def cpu_sum(self, name, value):
        self.gauge("{}.cpu_sum".format(name), value)

    def mem_max(self, name, value):
        self.gauge("{}.mem_max".format(name), value)

    def mem_sum(self, name, value):
        self.gauge("{}.mem_sum".format(name), value)

    def mem_pct_max(self, name, value):
        self.gauge("{}.mem_pct_max".format(name), value)

    def mem_pct_sum(self, name, value):
        self.gauge("{}.mem_pct_sum".format(name), value)
