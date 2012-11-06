import unittest

from tsuru.stream import Stream


class StreamTestCase(unittest.TestCase):
    def test_should_have_the_close_method(self):
        self.assertTrue(hasattr(Stream, "close"))
