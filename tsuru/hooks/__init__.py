# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

# tsuru-circus isn't responsible for running hooks anymore, this file is kept
# only for circus.ini in file in old platforms to remain compatible.
# tsuru-unit-agent is now responsible for running these hooks.


def before_start(*args, **kwargs):
    return True


def after_start(*args, **kwargs):
    return True
