# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import re
import time

from socket import gethostname

import requests

from circus.plugins import CircusPlugin
from honcho.procfile import Procfile
from zmq.eventloop import ioloop

from tsuru import common


def replace_args(data, **options):
    fmt_options = {}
    for key, value in options.items():
        key = key.lower()
        fmt_options[key] = value

    match = re.compile(r'\$([\w\.]+)|\$\{([\w\.]+)\}', re.I)

    def _repl(matchobj):
        option = None

        for result in matchobj.groups():
            if result is not None:
                option = result.lower()
                break

        if option in fmt_options:
            return str(fmt_options[option])

        return matchobj.group()
    return match.sub(_repl, data)


class FileWatcher(object):
    def __init__(self, filename, callback):
        self._filename = filename
        self._callback = callback
        self._mtime = 0

    def __call__(self, *args, **kwargs):
        if os.path.exists(self._filename):
            mtime = os.path.getmtime(self._filename)
            if mtime > self._mtime:
                self._mtime = mtime
                self._callback()


class ApprcWatcher(CircusPlugin):
    name = "apprc_watcher"

    def __init__(self, *args, **config):
        super(ApprcWatcher, self).__init__(*args, **config)
        self.loop_rate = int(config.get("loop_rate", 3))
        self.apprc = config.get("apprc", "/home/application/apprc")
        self.port = config.get("port", "8888")
        self.period = ioloop.PeriodicCallback(
            FileWatcher(self.apprc, self.reload_env),
            self.loop_rate * 1000,
            self.loop
        )

    def handle_init(self):
        self.period.start()

    def handle_stop(self):
        self.period.stop()

    def handle_recv(self, data):
        pass

    def reload_env(self):
        envs = {"port": self.port, "PORT": self.port}
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
            self.call("stop", name=name, waiting=True)
            self.call("set", name=name, options={"env": values})
            self.call("start", name=name, waiting=True)

    def cmds(self):
        return self.call("status")["statuses"].keys()


class WatcherCreationError(Exception):
    pass


class ProcfileWatcher(CircusPlugin):
    name = "procfile_watcher"

    def __init__(self, *args, **config):
        super(ProcfileWatcher, self).__init__(*args, **config)
        self.procfile_path = config.get("app_path",
                                        "/home/application/current/Procfile")
        self.working_dir = config.get("working_dir",
                                      "/home/application/current")
        self.apprc = config.get("apprc", "/home/application/apprc")
        self.port = config.get("port", "8888")
        self.uid = config.get("uid", "ubuntu")
        self.gid = config.get("gid", self.uid)
        self.stderr_stream = {"class": config.get("stderr_stream",
                                                  "tsuru.stream.Stream")}
        self.stdout_stream = {"class": config.get("stdout_stream",
                                                  "tsuru.stream.Stream")}
        self.ran = False

    def handle_init(self):
        pass

    def handle_stop(self):
        pass

    def handle_recv(self, data):
        while not self.ran:
            try:
                self.reload_procfile()
                self.ran = True
                break
            except:
                time.sleep(1)

    def load_envs(self):
        env = {"port": self.port, "PORT": self.port}
        env.update(common.load_envs(self.apprc))
        return env

    def add_watcher(self, name, cmd):
        env = self.load_envs()
        cmd = replace_args(cmd, **env)
        stderr_stream = self.stderr_stream.copy()
        stdout_stream = self.stdout_stream.copy()
        stdout_stream["watcher_name"] = stderr_stream["watcher_name"] = name
        options = {
            "env": env,
            "copy_env": True,
            "working_dir": self.working_dir,
            "stderr_stream": stderr_stream,
            "stdout_stream": stdout_stream,
            "uid": self.uid,
            "gid": self.gid,
        }
        result = self.call("add", cmd=cmd, name=name, options=options,
                           start=True, waiting=True)
        if not result or not isinstance(result, dict):
            raise WatcherCreationError()
        status = result.get("status")
        if status != "ok":
            raise WatcherCreationError()

    def commands(self, procfile):
        cmds = self.call("status")["statuses"]
        if "tsuru-hooks" in cmds:
            del cmds["tsuru-hooks"]
        cmds_names = set([k for k in cmds.keys()
                          if not k.startswith("plugin:")])
        new_cmds = set(procfile.commands.keys())
        return new_cmds.difference(cmds_names)

    def reload_procfile(self):
        with open(self.procfile_path) as file:
            procfile = Procfile(file.read())
            to_add = self.commands(procfile)
            for name in to_add:
                self.add_watcher(name=name, cmd=procfile.commands[name])


class StatusReporter(CircusPlugin):
    name = "status_reporter"

    def __init__(self, *args, **config):
        super(StatusReporter, self).__init__(*args, **config)
        self.loop_rate = int(config.get("loop_rate", 60))
        self.apprc = config.get("apprc", "/home/application/apprc")
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
        if "tsuru-hooks" in cmds:
            del cmds["tsuru-hooks"]
        status = "started"
        for cmd_name, cmd_status in cmds.iteritems():
            if cmd_name.startswith("plugin:"):
                continue
            if cmd_status != "active":
                status = "error"
                break
        envs = common.load_envs(self.apprc)
        url_data = {"host": envs.get("TSURU_HOST"),
                    "appname": envs.get("TSURU_APPNAME"),
                    "unitname": self.hostname}
        url = "{host}/apps/{appname}/units/{unitname}"
        token = envs.get("TSURU_APP_TOKEN")
        requests.post(url.format(**url_data), data={"status": status},
                      headers={"Authorization": "bearer " + token})
