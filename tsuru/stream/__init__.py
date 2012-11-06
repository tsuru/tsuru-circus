import os
import requests


class Stream(object):

    def __init__(self, **kwargs):
        pass

    def __call__(self, data):
        host = os.environ["TSURU_HOST"]
        appname = os.environ["APPNAME"]
        url = "{0}/apps/{1}/log".format(host, appname)
        requests.post(url, data=data)

    def close(self):
        pass
