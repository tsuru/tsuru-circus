# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import os

from circus.plugins import CircusPlugin
from circus.client import CircusClient
from honcho.procfile import Procfile
from zmq.eventloop import ioloop

from tsuru import common


class ApprcWatcher(CircusPlugin):
    name = "apprc_watcher"

    def __init__(self, *args, **config):
        super(ApprcWatcher, self).__init__(*args, **config)
        self.loop_rate = config.get("loop_rate", 10)  # in seconds
        self.apprc = config.get("apprc", "/home/application/apprc")
        self.port = config.get("port", "8888")
        self.period = ioloop.PeriodicCallback(self.look_after,
                                              self.loop_rate * 1000,
                                              self.loop)

    def handle_init(self):
        self.period.start()

    def handle_stop(self):
        self.period.stop()

    def handle_recv(self, data):
        pass

    def look_after(self):
        if os.path.exists(self.apprc):
            envs = {"port": self.port}
            envs.update(common.load_envs(self.apprc))
            for name in self.cmds():
                if not name.startswith("plugin:"):
                    self.add_envs(name, envs)

    def add_envs(self, name, envs):
        current = self.call("options", name=name)["options"]["env"]
        values = {}
        values.update(os.environ, **envs)
        if "PYTHONPATH" in values and "PYTHONPATH" not in envs:
            del values["PYTHONPATH"]
        if values != current:
            self.call("set", name=name, options={"env": values})

    def cmds(self):
        return self.call("status")["statuses"].keys()


class ProcfileWatcher(CircusPlugin):
    name = "procfile_watcher"

    def __init__(self, *args, **config):
        super(ProcfileWatcher, self).__init__(*args, **config)
        self.loop_rate = config.get("loop_rate", 10)  # in seconds
        self.procfile_path = config.get("app_path",
                                        "/home/application/current/Procfile")
        self.working_dir = config.get("working_dir",
                                      "/home/application/current")
        self.apprc = config.get("apprc", "/home/application/apprc")
        self.port = config.get("port", "8888")
        self.uid = config.get("uid", "ubuntu")
        self.stderr_stream = {"class": config.get("stderr_stream",
                                                  "tsuru.stream.Stream")}
        self.stdout_stream = {"class": config.get("stdout_stream",
                                                  "tsuru.stream.Stream")}
        self.period = ioloop.PeriodicCallback(self.look_after,
                                              self.loop_rate * 1000,
                                              self.loop)
        self.circus_client = CircusClient()

    def get_cmd(self, name):
        return self.call("get", name=name, keys=["cmd"])["options"]["cmd"]

    def handle_init(self):
        self.period.start()

    def handle_stop(self):
        self.period.stop()

    def handle_recv(self, data):
        pass

    def add_watcher(self, name, cmd):
        env = {"port": self.port}
        env.update(common.load_envs(self.apprc))
        options = {
            "env": env,
            "copy_env": True,
            "working_dir": self.working_dir,
            "stderr_stream": self.stderr_stream,
            "stdout_stream": self.stdout_stream,
            "uid": self.uid,
        }
        self.circus_client.call(json.dumps({
            "command": "add",
            "properties": {
                "cmd": cmd,
                "name": name,
                "args": [],
                "options": options,
                "start": True,
            },
        }))

    def remove_watcher(self, name):
        self.call("rm", name=name)

    def change_cmd(self, name, cmd):
        self.call("set", name=name, options={"cmd": cmd})

    def commands(self, procfile):
        cmds = self.call("status")["statuses"]
        cmds_names = set([k for k in cmds.keys() if not k.startswith("plugin:")])
        new_cmds = set(procfile.commands.keys())
        to_remove = cmds_names.difference(new_cmds)
        to_add = new_cmds.difference(cmds_names)
        to_change_names = cmds_names.intersection(new_cmds)
        to_change = {}
        for name in to_change_names:
            if self.get_cmd(name) != procfile.commands.get(name):
                to_change[name] = procfile.commands[name]
        return to_add, to_remove, to_change

    def look_after(self):
        if os.path.exists(self.procfile_path):
            with open(self.procfile_path) as file:
                procfile = Procfile(file.read())
                to_add, to_remove, to_change = self.commands(procfile)

                for name in to_remove:
                    self.remove_watcher(name)

                for name in to_add:
                    self.add_watcher(name=name, cmd=procfile.commands[name])

                for name, cmd in to_change.items():
                    self.change_cmd(name=name, cmd=procfile.commands[name])
