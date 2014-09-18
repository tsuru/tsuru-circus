# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import tsuru_unit_agent.stream


# All implementation has moved to tsuru-unit-agent, this class is only defined
# here so that we don't break existing circus.ini files.
class Stream(tsuru_unit_agent.stream.Stream):
    pass
