import json
import os
import re
import requests


def extract_message(msg):
    regex = "\[\w+\]\ " #like [INFO]
    msg = re.split(regex, msg)[-1]
    return msg.replace("\n", "")


class Stream(object):

    def __init__(self, **kwargs):
        pass

    def __call__(self, data):
        host = os.environ.get("TSURU_HOST", None)
        appname = os.environ.get("APPNAME", None)
        if appname and host:
            url = "{0}/apps/{1}/log".format(host, appname)
            messages = [data["data"],]
            requests.post(url, data=json.dumps(messages))

    def close(self):
        pass
