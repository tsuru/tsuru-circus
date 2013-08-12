# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import yaml
import os


def load_config(config_file):
    with open(config_file) as f:
        return yaml.load(f.read())


def before_start(*args, **kwargs):
    config = load_config()
    os.system(config['pre-restart'][0])
