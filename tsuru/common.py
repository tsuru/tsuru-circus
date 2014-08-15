# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import re

regexp_quotes = re.compile(r'^"(.*)"$')


def load_envs(path):
    envs = {}
    if os.path.exists(path):
        with open(path) as file:
            for line in file.readlines():
                if "export" in line:
                    line = line.replace("export ", "")
                    k, v = line.split("=", 1)
                    v = v.replace("\n", "")
                    match = regexp_quotes.match(v)
                    if match:
                        v = match.groups()[0]
                    envs[k] = v
    return envs
