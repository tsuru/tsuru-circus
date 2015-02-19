# Copyright 2015 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os

from socket import gethostname

import requests

from circus.plugins import CircusPlugin
from zmq.eventloop import ioloop


class ProcfileWatcher(CircusPlugin):
    name = "procfile_watcher"

    def handle_recv(self, data):
        pass


class StatusReporter(CircusPlugin):
    name = "status_reporter"

    def __init__(self, *args, **config):
        super(StatusReporter, self).__init__(*args, **config)
        self.loop_rate = int(config.get("loop_rate", 60))
        self.hostname = gethostname()
        self.period = ioloop.PeriodicCallback(self.report,
                                              self.loop_rate * 1000,
                                              self.loop)

    def handle_init(self):
        self.period.start()

    def handle_stop(self):
        self.period.stop()

    def handle_recv(self, data):
        pass

    def report(self):
        cmds = self.call("status")["statuses"]
        status = "started"
        for cmd_name, cmd_status in cmds.iteritems():
            if cmd_name.startswith("plugin:"):
                continue
            if cmd_status != "active":
                status = "error"
                break
        envs = os.environ
        url_data = {"host": envs.get("TSURU_HOST"),
                    "appname": envs.get("TSURU_APPNAME"),
                    "unitname": self.hostname}
        url = "{host}/apps/{appname}/units/{unitname}"
        token = envs.get("TSURU_APP_TOKEN")
        requests.post(url.format(**url_data), data={"status": status},
                      headers={"Authorization": "bearer " + token})
