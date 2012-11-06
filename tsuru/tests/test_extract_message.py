import unittest

from tsuru.stream import extract_message


class ExtractMessageTestCase(unittest.TestCase):
    def test_remove_breaklines_from_message(self):
        # msg = '2012-11-06 17:13:55 [12019] [INFO] Starting gunicorn 0.15.0\n'
        msg = 'Starting gunicorn 0.15.0\n'
        result = extract_message(msg)
        self.assertEqual(msg.replace("\n", ""), result)

    def test_extract_message(self):
        msg = '2012-11-06 17:13:55 [12019] [INFO] Starting gunicorn 0.15.0'
        expected = 'Starting gunicorn 0.15.0'
        result = extract_message(msg)
        self.assertEqual(expected, result)
