import requests


class Stream(object):

    def __init__(self, **kwargs):
        pass

    def __call__(self, data):
        requests.post("url", data=data)

    def close(self):
        pass
