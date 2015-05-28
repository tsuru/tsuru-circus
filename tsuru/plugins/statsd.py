# Copyright 2015 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from zmq.eventloop import ioloop

from circus.plugins import CircusPlugin
from circus.util import human2bytes
from tsuru.plugins.stats.statsd import StatsdBackend
from tsuru.plugins.stats.logstash import LogstashBackend
from tsuru.plugins.stats.fake import FakeBackend

import psutil
import os


storages = {
    "fake": FakeBackend,
    "statsd": StatsdBackend,
    "logstash": LogstashBackend,
}


class StatsdEmitter(CircusPlugin):
    name = 'statsd'
    default_app_name = "app"

    def __init__(self, endpoint, pubsub_endpoint, check_delay, ssh_server,
                 **config):
        super(StatsdEmitter, self).__init__(endpoint, pubsub_endpoint,
                                            check_delay, ssh_server=ssh_server)

        self.storage = self.get_storage()

    def get_storage(self):
        default_backend = "statsd"
        storage = os.environ.get("TSURU_METRICS_BACKEND", default_backend)

        # when a backend does not exists the default should be returned
        if storage not in storages:
            storage = default_backend

        return storages[storage]()

    def handle_recv(self, data):
        pass

    def stop(self):
        self.storage.stop()
        super(StatsdEmitter, self).stop()


class BaseObserver(StatsdEmitter):

    def __init__(self, *args, **config):
        super(BaseObserver, self).__init__(*args, **config)
        self.loop_rate = float(config.get("loop_rate", 20))  # in seconds

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

    def connections(self):
        result = psutil.net_connections("tcp")
        conns = []

        for conn in result:
            if conn.status == "ESTABLISHED" and conn.raddr[0] != "127.0.0.1":
                ip, port = conn.raddr

                if conn.laddr[1] == 8888:
                    ip = "127.0.0.1"
                    port = conn.laddr[1]

                conns.append("{}:{}".format(ip, port))

        return conns

    def look_after(self):
        self.storage.disk_usage(self.disk_usage())

        net_sent, net_recv = self.net_io()
        self.storage.net_sent(net_sent)
        self.storage.net_recv(net_recv)

        self.storage.net_connections(self.connections_established())
        self.storage.connections(self.connections())

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
