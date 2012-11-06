import unittest
import mock

from tsuru.stream import Stream


class StreamTestCase(unittest.TestCase):
    def test_should_have_the_close_method(self):
        self.assertTrue(hasattr(Stream, "close"))

    def test_should_send_log_to_tsuru(self):
        stream = Stream()
        with mock.patch("requests.post") as post:
            post.return_value = mock.Mock(status_code=200)
            stream("data")
            post.assert_called_with("url", data="data")
