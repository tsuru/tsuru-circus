# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from circus.plugins import CircusPlugin
from circus.client import CircusClient
from zmq.eventloop import ioloop
from honcho.procfile import Procfile

import os.path
import json


class ProcfileWatcher(CircusPlugin):
    name = "procfile_watcher"

    def __init__(self, *args, **config):
        super(ProcfileWatcher, self).__init__(*args, **config)
        self.loop_rate = config.get("loop_rate", 60)  # in seconds
        self.procfile_path = config.get("app_path", "/home/application/current/Procfile")
        self.period = ioloop.PeriodicCallback(self.look_after, self.loop_rate * 1000, self.loop)
        self.circus_client = CircusClient()

    def handle_init(self):
        self.period.start()

    def handle_stop(self):
        self.period.stop()

    def handle_recv(self, data):
        pass

    def add_watcher(self, name, cmd):
        options = {
            "shell": True,
            "working_dir": "/home/application/current",
            "stderr_stream": {"class": "tsuru.stream.Stream"},
            "stdout_stream": {"class": "tsuru.stream.Stream"},
        }
        self.circus_client.call(json.dumps({
            "command": "add",
            "properties": {
            "cmd":  cmd,
            "name": name,
            "args": [],
            "options": options,
            "start": True,
        }}))

    def remove_watcher(self, name):
        self.call("rm", name=name)

    def commands(self, procfile):
        cmds = set(self.call("status")["statuses"].keys())
        new_cmds = set(procfile.commands.keys())
        to_remove = cmds.difference(new_cmds)
        to_add = new_cmds.difference(cmds)
        return to_add, to_remove

    def look_after(self):
        if os.path.exists(self.procfile_path):
            with open(self.procfile_path) as file:
                procfile = Procfile(file.read())
                to_add, to_remove = self.commands(procfile)

                for name in to_remove:
                    self.remove_watcher(name)

                for name in to_add:
                    self.add_watcher(name=name, cmd=procfile.commands[name])
