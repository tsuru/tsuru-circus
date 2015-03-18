# Copyright 2015 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.


class FakeBackend(object):

    def __init__(self):
        self.gauges = []

    def stop(self):
        pass

    def gauge(self, key, value):
        self.gauges.append((key, value))

    def disk_usage(self, value):
        self.gauge("disk_usage", value)

    def net_sent(self, value):
        self.gauge("net.sent", value)

    def net_recv(self, value):
        self.gauge("net.recv", value)

    def net_connections(self, value):
        self.gauge("net.connections", value)

    def connections(self, conns):
        for conn in conns:
            self.gauge("connection", conn)

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
