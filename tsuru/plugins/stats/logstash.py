# Copyright 2015 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import socket


class LogstashBackend(object):

    def __init__(self):
        envs = os.environ

        self.app_name = envs.get("TSURU_APPNAME")
        self.host_name = socket.gethostname()

        # initialize measure
        host = envs.get("LOGSTASH_HOST") or 'localhost'
        port = envs.get("LOGSTASH_PORT") or '1984'

        from measures import Measure
        self.client = Measure(envs.get("LOGSTASH_CLIENT", "tsuru"), (host, int(port)))

    def stop(self):
        pass

    def gauge(self, key, value):
        dimensions = {"app": self.app_name, "host": self.host_name, "value": float(value)}
        self.client.count(key, dimensions=dimensions)

    def disk_usage(self, value):
        self.gauge("disk_usage", value)

    def net_sent(self, value):
        self.gauge("net_sent", value)

    def net_recv(self, value):
        self.gauge("net_recv", value)

    def net_connections(self, value):
        self.gauge("net_connections", value)

    def connections(self, connection_list):
        for conn in connection_list:
            dimensions = {"app": self.app_name, "host": self.host_name, "connection": conn}
            self.client.count("connection", dimensions=dimensions)

    def cpu_max(self, name, value):
        self.gauge("cpu_max", value)

    def cpu_sum(self, name, value):
        self.gauge("cpu_sum", value)

    def mem_max(self, name, value):
        self.gauge("mem_max", value)

    def mem_sum(self, name, value):
        self.gauge("mem_sum", value)

    def mem_pct_max(self, name, value):
        self.gauge("mem_pct_max", value)

    def mem_pct_sum(self, name, value):
        self.gauge("mem_pct_sum", value)
