import unittest
import mock
import os

from tsuru.stream import Stream


class StreamTestCase(unittest.TestCase):
    def test_should_have_the_close_method(self):
        self.assertTrue(hasattr(Stream, "close"))

    def test_should_send_log_to_tsuru(self):
        host = "http://someurl.com"
        appname = "myapp"
        os.environ["TSURU_HOST"] = host
        os.environ["APPNAME"] = appname
        stream = Stream()
        with mock.patch("requests.post") as post:
            post.return_value = mock.Mock(status_code=200)
            stream("data")
            url = "{0}/apps/{1}/log".format(host, appname)
            post.assert_called_with(url, data="data")

    def test_should_slience_errors_when_envs_does_not_exist(self):
        del os.environ["TSURU_HOST"]
        del os.environ["APPNAME"]
        stream = Stream()
        try:
            stream("data")
        except:
            assert False
