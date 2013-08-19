# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import yaml
import subprocess


def load_config(**kwargs):
    watcher = kwargs.get("watcher")
    files_name = ["app.yaml", "app.yml"]
    for file_name in files_name:
        try:
            with open(os.path.join(watcher.working_dir, file_name)) as f:
                return yaml.load(f.read())
        except IOError:
            pass
    return {
        'hooks': {
            'pre-restart': [],
            'post-restart': [],
        }
    }


def run_commands(name, **kwargs):
    config = load_config(**kwargs)
    watcher = kwargs.get("watcher")
    for command in config['hooks'][name]:
        result = subprocess.check_output([command], shell=True)
        from tsuru.stream import Stream
        Stream(watcher_name=watcher.name)(
            {"data": " ---> Running {}".format(name)})
        Stream(watcher_name=watcher.name)({"data": result})


def before_start(*args, **kwargs):
    run_commands('pre-restart', **kwargs)


def after_start(*args, **kwargs):
    run_commands('post-restart')
