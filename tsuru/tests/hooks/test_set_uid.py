# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest

import mock

from tsuru.hooks import set_uid


class Bag(object):
    pass


class SetUIDTestCase(unittest.TestCase):

    @mock.patch("pwd.getpwnam")
    @mock.patch("os.setuid")
    @mock.patch("os.setgid")
    def test_set_uid_from_watcher(self, setgid, setuid, getpwnam):
        passwd = Bag()
        passwd.pw_uid = 500
        passwd.pw_gid = 500
        watcher = Bag()
        watcher.uid = "ubuntu"
        getpwnam.return_value = passwd
        fn = set_uid(watcher)
        fn()
        getpwnam.assert_called_with("ubuntu")
        setuid.assert_called_with(500)
        setgid.assert_called_with(500)
