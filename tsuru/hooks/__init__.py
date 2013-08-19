# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import yaml
import subprocess


def load_config():
    files_name = ["app.yaml", "app.yml"]
    for file_name in files_name:
        try:
            with open(file_name) as f:
                return yaml.load(f.read())
        except IOError:
            pass
    return {
        'hooks': {
            'pre-restart': [],
            'post-restart': [],
        }
    }


def run_commands(hook_name):
    config = load_config()
    for command in config['hooks'][hook_name]:
        result = subprocess.check_output([command], shell=True)


def before_start(*args, **kwargs):
    run_commands('pre-restart')


def after_start(*args, **kwargs):
    run_commands('post-restart')
