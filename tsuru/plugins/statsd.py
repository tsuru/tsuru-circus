# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os

from zmq.eventloop import ioloop

from circus.plugins import CircusPlugin
from circus.util import human2bytes

from tsuru import common


class StatsdEmitter(CircusPlugin):
    name = 'statsd'
    default_app_name = "app"

    def __init__(self, endpoint, pubsub_endpoint, check_delay, ssh_server,
                 **config):
        super(StatsdEmitter, self).__init__(endpoint, pubsub_endpoint,
                                            check_delay, ssh_server=ssh_server)
        self.app = config.get('application_name', self.default_app_name)

        apprc = "/home/application/apprc"
        envs = common.load_envs(apprc)

        app_name = envs.get("TSURU_APPNAME")
        host_name = os.environ.get("HOSTNAME")
        # tsuru.app.host
        self.prefix = 'tsuru.{}.{}'.format(app_name, host_name)

        # initialize statsd
        from circus.plugins.statsd import StatsdClient
        host = envs.get("STATSD_HOST") or config.get('host', 'localhost')
        port = envs.get("STATSD_PORT") or config.get('port', '8125')

        self.statsd = StatsdClient(
            host=host,
            port=int(port),
            prefix=self.prefix,
            sample_rate=float(config.get('sample_rate', '1.0'))
        )

    def handle_recv(self, data):
        watcher_name, action, msg = self.split_data(data)
        self.statsd.increment('{}.{}'.format(watcher_name, action))

    def stop(self):
        self.statsd.stop()
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
        self.statsd.stop()

    def handle_recv(self, data):
        pass

    def look_after(self):
        raise NotImplementedError()


class Stats(BaseObserver):

    name = 'stats'

    def look_after(self):
        info = self.call("stats")
        if info["status"] == "error":
            self.statsd.increment("_stats.error")
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
                    cpus.append(sub_info['cpu'])
                    mems.append(sub_info['mem'])
                    mem_infos.append(human2bytes(sub_info['mem_info1']))
                elif sub_name == "spawn_count":
                    # spawn_count info is in the same level as processes
                    # dict infos, so if spawn_count is given, take it and
                    # continue
                    self.statsd.gauge("{}.spawn_count".format(name),
                                      sub_info)

                self.statsd.gauge("{}.watchers_num".format(name), len(cpus))

                if not cpus:
                    # if there are only dead processes, we have an empty list
                    # and we can't measure it
                    continue

                self.statsd.gauge("{}.cpu_max".format(name), max(cpus))
                self.statsd.gauge("{}.cpu_sum".format(name), sum(cpus))
                self.statsd.gauge("{}.mem_pct_max".format(name), max(mems))
                self.statsd.gauge("{}.mem_pct_sum".format(name), sum(mems))
                self.statsd.gauge("{}.mem_max".format(name), max(mem_infos))
                self.statsd.gauge("{}.mem_sum".format(name), sum(mem_infos))
