# Copyright 2014 tsuru-circus authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import re
import requests
import logging

from logging.handlers import SysLogHandler
from socket import SOCK_DGRAM, SOCK_STREAM, gethostname
from tsuru import common
from datetime import datetime


def extract_message(msg):
    # 2012-11-06 18:30:10 [13887] [INFO]
    regex = "\d+\-\d+\-\d+ \d+\:\d+\:\d+ \[\d+\] \[\w+\] "
    msgs = re.split(regex, msg)
    return [m for m in msgs if m]


class Stream(object):

    def __init__(self, **kwargs):
        self._buffer = ""
        self._max_buffer_size = kwargs.get("max_buffer_size", 10240)
        self.apprc = "/home/application/apprc"
        self.watcher_name = kwargs.get("watcher_name", "")
        self.timeout = kwargs.get("timeout", 2)
        self.hostname = gethostname()

    def __call__(self, data):
        (appname, host, token, syslog_server, syslog_port,
         syslog_facility, syslog_socket) = self.load_envs()
        if appname and host and token:
            self.log_tsuru_api(data, appname, host, token)
        if syslog_server and syslog_port and syslog_facility:
            self.log_syslog(data, appname, syslog_server, syslog_port,
                            syslog_facility, syslog_socket)

    def log_tsuru_api(self, data, appname, host, token):
        url = "{0}/apps/{1}/log?source={2}&unit={3}".format(host, appname,
                                                            self.watcher_name,
                                                            self.hostname)
        messages = self.get_messages(data["data"])
        try:
            requests.post(url, data=json.dumps(messages),
                          headers={"Authorization": "bearer " + token},
                          timeout=self.timeout)
        except:
            pass

    def log_syslog(self, data, appname, host, port, facility, socket):
        messages = self.get_messages(data["data"])
        if socket == 'tcp':
            socket_type = SOCK_STREAM
        else:
            socket_type = SOCK_DGRAM
        try:
            date_time = datetime.now().strftime("%b %d %H:%M:%S")\
                                      .lstrip("0").replace(" 0", "  ")
            logger = logging.getLogger(appname)
            logger.handlers = []
            logger.setLevel(logging.INFO)
            syslog = SysLogHandler(address=(host, int(port)),
                                   facility=facility, socktype=socket_type)
            formatter = logging.Formatter('{0} {1} %(name)s:\
                                           %(message)s'.format(date_time,
                                                               self.hostname))
            syslog.setFormatter(formatter)
            logger.addHandler(syslog)
            for m in messages:
                if data["name"] == 'stdout':
                    logger.info(m)
                else:
                    logger.error(m)
        except:
            pass

    def load_envs(self):
        envs = common.load_envs(self.apprc)
        return (envs.get("TSURU_APPNAME"), envs.get("TSURU_HOST"),
                envs.get("TSURU_APP_TOKEN"), envs.get("TSURU_SYSLOG_SERVER"),
                envs.get("TSURU_SYSLOG_PORT"),
                envs.get("TSURU_SYSLOG_FACILITY"),
                envs.get("TSURU_SYSLOG_SOCKET"))

    def close(self):
        pass

    def get_messages(self, msg):
        result = []
        if self._buffer != "":
            msg = self._buffer + msg
            self._buffer = ""
        msgs = extract_message(msg)
        lines = "".join(msgs).splitlines(True)
        for line in lines:
            if (line.endswith("\n") or len(line) > self._max_buffer_size):
                result.append(line)
            else:
                self._buffer = line
        return result
