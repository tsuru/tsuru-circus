# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import re
import requests

from tsuru import common


def extract_message(msg):
    # 2012-11-06 18:30:10 [13887] [INFO]
    regex = "\d+\-\d+\-\d+ \d+\:\d+\:\d+ \[\d+\] \[\w+\] "
    msgs = re.split(regex, msg)
    return [m for m in msgs if m]


class Stream(object):

    def __init__(self, **kwargs):
        self.apprc = "/home/application/apprc"
        self.watcher_name = kwargs.get("watcher_name", "")

    def __call__(self, data):
        appname, host, token = self.load_envs()
        if appname and host and token:
            url = "{0}/apps/{1}/log?source={2}".format(host, appname,
                                                       self.watcher_name)
            messages = extract_message(data["data"])
            requests.post(url, data=json.dumps(messages),
                          headers={"Authorization": "bearer " + token})

    def load_envs(self):
        envs = common.load_envs(self.apprc)
        return (envs.get("TSURU_APPNAME"), envs.get("TSURU_HOST"),
                envs.get("TSURU_APP_TOKEN"))

    def close(self):
        pass
