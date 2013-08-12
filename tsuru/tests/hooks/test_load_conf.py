# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from tempfile import NamedTemporaryFile

from tsuru.hooks import load_config


class LoadConfTest(TestCase):
    def setUp(self):
        data = u"""hooks:
pre-restart:
  - testdata/pre.sh
post-restart:
  - testdata/pos.sh"""
        self.yaml_file = NamedTemporaryFile()
        self.yaml_file.write(data)
        self.yaml_file.flush()

    def tearDown(self):
        self.yaml_file.close()

    def test_load(self):
        config = load_config(self.yaml_file.name)
        expected = {
            'hooks': None,
            'pre-restart': ['testdata/pre.sh'],
            'post-restart': ['testdata/pos.sh'],
        }
        self.assertDictEqual(config, expected)
