# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import pwd
import subprocess

import yaml


def load_config(**kwargs):
    watcher = kwargs.get("watcher")
    files_name = ["app.yaml", "app.yml"]
    for file_name in files_name:
        try:
            with open(os.path.join(watcher.working_dir, file_name)) as f:
                return yaml.load(f.read())
        except IOError:
            pass
    return {}


def set_uid(watcher):
    def fn():
        pwnam = pwd.getpwnam(watcher.uid)
        gid = pwnam.pw_gid
        os.setgid(gid)
        uid = pwnam.pw_uid
        os.setuid(uid)
    return fn


def run_commands(name, **kwargs):
    from tsuru.stream import Stream
    config = load_config(**kwargs)
    watcher = kwargs.get("watcher")
    parts = name.split(":")
    cmds = config.get("hooks", {})
    for part in parts:
        cmds = cmds.get(part, {})
    if cmds:
        Stream(watcher_name=watcher.name)(
            {"data": " ---> Running {}".format(name)})
    for command in cmds:
        try:
            commands = ["/bin/bash", "-c"]
            cmd = "source /home/application/apprc && {}"
            commands.append(cmd.format(command))
            result = subprocess.check_output(commands,
                                             stderr=subprocess.STDOUT,
                                             cwd=watcher.working_dir,
                                             preexec_fn=set_uid(watcher))
            Stream(watcher_name=watcher.name)({"data": result})
        except subprocess.CalledProcessError as e:
            Stream(watcher_name=watcher.name)({"data": str(e)})
            Stream(watcher_name=watcher.name)({"data": e.output})
    return True


def before_start(*args, **kwargs):
    run_commands('restart:before-each', **kwargs)
    return run_commands('pre-restart', **kwargs)


def after_start(*args, **kwargs):
    run_commands('restart:after-each', **kwargs)
    return run_commands('post-restart', **kwargs)
