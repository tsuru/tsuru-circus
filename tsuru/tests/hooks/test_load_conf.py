# Copyright 2013 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase
from mock import Mock
import os

from tsuru.hooks import load_config


class LoadConfTest(TestCase):
    def setUp(self):
        self.working_dir = os.path.dirname(__file__)
        self.watcher = Mock(working_dir=self.working_dir)
        self.data = u"""hooks:
  pre-restart:
    - testdata/pre.sh
  post-restart:
    - testdata/pos.sh"""

    def test_load_app_yaml(self):
        yaml_file = os.path.join(self.working_dir, "app.yaml")
        with open(yaml_file, "w") as f:
            f.write(self.data)
        config = load_config(watcher=self.watcher)
        expected = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh'],
                'post-restart': ['testdata/pos.sh'],
            }
        }
        self.assertDictEqual(config, expected)
        os.remove(yaml_file)

    def test_load_app_yml(self):
        yml_file = os.path.join(self.working_dir, "app.yaml")
        with open(yml_file, "w") as f:
            f.write(self.data)
        config = load_config(watcher=self.watcher)
        expected = {
            'hooks': {
                'pre-restart': ['testdata/pre.sh'],
                'post-restart': ['testdata/pos.sh'],
            }
        }
        self.assertDictEqual(config, expected)
        os.remove(yml_file)

    def test_load_without_app_files(self):
        config = load_config(watcher=self.watcher)
        expected = {}
        self.assertDictEqual(config, expected)
