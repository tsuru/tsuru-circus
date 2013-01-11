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
        pass

    def __call__(self, data):
        host = os.environ.get("TSURU_HOST", None)
        appname = os.environ.get("TSURU_APPNAME", None)
        if appname and host:
            url = "{0}/apps/{1}/log".format(host, appname)
            messages = extract_message(data["data"])
            requests.post(url, data=json.dumps(messages))

    def close(self):
        pass
