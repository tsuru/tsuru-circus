from unittest import TestCase
from mock import Mock

from tsuru.plugins import ProcfileWatcher

from honcho.procfile import Procfile


class ProcfileWatcherTest(TestCase):
    def test_add_watcher(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        options = {
            "cmd": "ls",
            "name": "name",
            "start": True,
            "copy_env": True,
        }
        plugin.add_watcher(name=options["name"], cmd=options["cmd"])
        plugin.call.assert_called_with("add", **options)

    def test_remove_watcher(self):
        plugin = ProcfileWatcher("", "", 1)
        plugin.call = Mock()
        name = "name"
        plugin.remove_watcher(name=name)
        plugin.call.assert_called_with("rm", name=name)

    def test_commands(self):
        plugin = ProcfileWatcher("", "", 1)
        result = Mock()
        result.return_value = {"statuses": {}}
        plugin.call = result
        procfile = Procfile('web: gunicorn -b 0.0.0.0:8080 abyss.wsgi\n')
        to_add, to_remove = plugin.commands(procfile)
        plugin.call.assert_called_with("status")
