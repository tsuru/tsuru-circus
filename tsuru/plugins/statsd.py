# Copyright 2015 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import socket
import os

from zmq.eventloop import ioloop

from circus.plugins import CircusPlugin
from circus.util import human2bytes

import psutil


class StatsdEmitter(CircusPlugin):
    name = 'statsd'
    default_app_name = "app"

    def __init__(self, endpoint, pubsub_endpoint, check_delay, ssh_server,
                 **config):
        super(StatsdEmitter, self).__init__(endpoint, pubsub_endpoint,
                                            check_delay, ssh_server=ssh_server)

        self.storage = StatsdBackend()

    def handle_recv(self, data):
        pass

    def stop(self):
        self.storage.stop()
        super(StatsdEmitter, self).stop()


class BaseObserver(StatsdEmitter):

    def __init__(self, *args, **config):
        super(BaseObserver, self).__init__(*args, **config)
        self.loop_rate = float(config.get("loop_rate", 60))  # in seconds

    def handle_init(self):
        self.period = ioloop.PeriodicCallback(self.look_after,
                                              self.loop_rate * 1000, self.loop)
        self.period.start()

    def handle_stop(self):
        self.period.stop()

    def handle_recv(self, data):
        pass

    def look_after(self):
        raise NotImplementedError()


class StatsdBackend(object):

    def __init__(self):
        envs = os.environ

        app_name = envs.get("TSURU_APPNAME")
        host_name = socket.gethostname()
        # tsuru.app.host
        self.prefix = 'tsuru.{}.{}'.format(app_name, host_name)

        # initialize statsd
        from circus.plugins.statsd import StatsdClient
        host = envs.get("STATSD_HOST", 'localhost') or "localhost"
        port = envs.get("STATSD_PORT", '8125') or "8125"

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


class Stats(BaseObserver):

    name = 'stats'

    def disk_usage(self):
        return psutil.disk_usage("/").used

    def net_io(self):
        io = psutil.net_io_counters()
        return io.bytes_sent, io.bytes_recv

    def connections_established(self):
        connections = psutil.net_connections("tcp")
        return sum([1 for conn in connections if conn.status == "ESTABLISHED"])

    def look_after(self):
        self.storage.disk_usage(self.disk_usage())

        net_sent, net_recv = self.net_io()
        self.storage.net_sent(net_sent)
        self.storage.net_recv(net_recv)

        self.storage.net_connections(self.connections_established())

        info = self.call("stats")
        if info["status"] == "error":
            return
        for name, stats in info['infos'].items():
            if name.startswith("plugin:"):
                # ignore plugins
                continue

            cpus = []
            mems = []
            mem_infos = []

            for sub_name, sub_info in stats.items():
                if isinstance(sub_info, dict):
                    cpu = [sub_info['cpu']]
                    mem = [sub_info['mem']]
                    inf = [human2bytes(sub_info['mem_info1'])]

                    for p in sub_info['children']:
                        cpu.append(p['cpu'])
                        mem.append(p['mem'])
                        inf.append(human2bytes(p['mem_info1']))

                    cpus.append(sum(cpu))
                    mems.append(sum(mem))
                    mem_infos.append(sum(inf))

                if not cpus:
                    # if there are only dead processes, we have an empty list
                    # and we can't measure it
                    continue

                self.storage.cpu_max(name, max(cpus))
                self.storage.cpu_sum(name, sum(cpus))
                self.storage.mem_pct_max(name, max(mems))
                self.storage.mem_pct_sum(name, sum(mems))
                self.storage.mem_max(name, max(mem_infos))
                self.storage.mem_sum(name, sum(mem_infos))
