from circus.plugins import CircusPlugin
from zmq.eventloop import ioloop
from honcho.procfile import Procfile

import os.path


class ProcfileWatcher(CircusPlugin):
    name = "procfile_watcher"

    def __init__(self, *args, **config):
        super(ProcfileWatcher, self).__init__(*args, **config)
        self.loop_rate = config.get("loop_rate", 1)  # in seconds
        self.procfile_path = config.get("app_path", "/home/application/current/Procfile")
        self.period = ioloop.PeriodicCallback(self.look_after, self.loop_rate * 1000, self.loop)

    def handle_init(self):
        self.period.start()

    def handle_stop(self):
        self.period.stop()

    def handle_recv(self, data):
        pass

    def add_watcher(self, name, cmd):
        options = {
            "name": name,
            "cmd": cmd,
            "start": True,
            "copy_env": True,
        }
        self.call("add", **options)

    def remove_watcher(self, name):
        self.call("rm", name=name)

    def commands(self, data):
        procfile = Procfile(data)
        cmds = set(self.call("status")["statuses"].keys())
        new_cmds = set(procfile.commands.keys())
        to_remove = cmds.difference(new_cmds)
        to_add = new_cmds.difference(cmds)
        return to_add, to_remove

    def look_after(self):
        if os.path.exists(self.procfile_path):
            with open(self.procfile_path) as file:
                to_add, to_remove = self.commands(file.read())

                for name in to_remove:
                    self.remove_watcher(name)

                for name in to_add:
                    self.add_watcher(name=name, cmd=procfile.commands[name])
