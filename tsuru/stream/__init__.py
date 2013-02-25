# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import os
import re
import requests


def extract_message(msg):
    regex = "\d+\-\d+\-\d+ \d+\:\d+\:\d+ \[\d+\] \[\w+\] " #like 2012-11-06 18:30:10 [13887] [INFO]
    msgs = re.split(regex, msg)
    return [msg for msg in msgs if msg] #removing empty entries


class Stream(object):

    def __init__(self, **kwargs):
        self.apprc = "/home/application/apprc"

    def __call__(self, data):
        tsuru_appname, tsuru_host = self.appname_and_host()
        if tsuru_appname and tsuru_host:
            url = "{0}/apps/{1}/log".format(tsuru_host, tsuru_appname)
            messages = extract_message(data["data"])
            requests.post(url, data=json.dumps(messages))

    def appname_and_host(self):
        envs = self.load_envs()
        return envs.get("TSURU_APPNAME"), envs.get("TSURU_HOST")

    def load_envs(self):
        envs = {}
        with open(self.apprc) as file:
            for line in file.readlines():
                if "export" in line:
                    line = line.replace("export ", "")
                    k, v = line.split("=")
                    v = v.replace("\n", "").replace('"', '')
                    envs[k] = v
        return envs

    def close(self):
        pass
