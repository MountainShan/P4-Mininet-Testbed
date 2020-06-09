#!/usr/bin/env python

# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#
# Antonin Bas (antonin@barefootnetworks.com)
#
#

import sys
import md5

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.protocol import TMultiplexedProtocol

def check_JSON_md5(client, json_src, out=sys.stdout):
    with open(json_src, 'r') as f:
        m = md5.new()
        for L in f:
            m.update(L)
        md5sum = m.digest()

    def my_print(s):
        out.write(s)

    bm_md5sum = client.bm_get_config_md5()

def get_json_config(standard_client=None, json_path=None, out=sys.stdout):
    if json_path:
        if standard_client is not None:
            check_JSON_md5(standard_client, json_path)
        with open(json_path, 'r') as f:
            return f.read()
    else:
        assert(standard_client is not None)
        try:
            json_cfg = standard_client.bm_get_config()
        except:
            sys.exit(1)
        return json_cfg

# services is [(service_name, client_class), ...]
def thrift_connect(thrift_ip, thrift_port, services, out=sys.stdout):
    transport = TSocket.TSocket(thrift_ip, thrift_port)
    transport = TTransport.TBufferedTransport(transport)
    bprotocol = TBinaryProtocol.TBinaryProtocol(transport)

    clients = []

    for service_name, service_cls in services:
        if service_name is None:
            clients.append(None)
            continue
        protocol = TMultiplexedProtocol.TMultiplexedProtocol(bprotocol, service_name)
        client = service_cls(protocol)
        clients.append(client)
    try:
        transport.open()
    except TTransport.TTransportException:
        sys.exit(1)
    return clients

