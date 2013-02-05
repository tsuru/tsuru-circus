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
        }
        self.call("add", **options)

    def remove_watcher(self, name):
        self.call("rm", name=name)

    def look_after(self):
        if os.path.exists(self.procfile_path):
            with open(self.procfile_path) as file:
                procfile = Procfile(file.read())
                commands = self.call("status")["statuses"].keys()
                for name, cmd in procfile.commands.items():
                    if name not in commands:
                        self.add_watcher(name=name, cmd=cmd)
