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

    def __call__(self, data):
        tsuru_appname, tsuru_host = self.appname_and_host()
        if tsuru_appname and tsuru_host:
            url = "{0}/apps/{1}/log".format(tsuru_host, tsuru_appname)
            messages = extract_message(data["data"])
            requests.post(url, data=json.dumps(messages))

    def appname_and_host(self):
        envs = common.load_envs(self.apprc)
        return envs.get("TSURU_APPNAME"), envs.get("TSURU_HOST")

    def close(self):
        pass
