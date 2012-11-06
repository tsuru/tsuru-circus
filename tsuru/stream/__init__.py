import os
import requests


class Stream(object):

    def __init__(self, **kwargs):
        pass

    def __call__(self, data):
        host = os.environ.get("TSURU_HOST", None)
        appname = os.environ.get("APPNAME", None)
        if appname and host:
            url = "{0}/apps/{1}/log".format(host, appname)
            requests.post(url, data=data)

    def close(self):
        pass
