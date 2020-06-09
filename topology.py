#!/usr/bin/python

import argparse
import os, sys, time
import subprocess
import random

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink, Intf
from mininet.node import RemoteController, OVSSwitch
from p4_topology.p4_mininet import P4Host
from p4_topology.p4runtime_switch import P4RuntimeSwitch



parser = argparse.ArgumentParser(description="P4 Mininet")
parser.add_argument("--bmv2", help="bmv2", type=str, action="store", required=True)
parser.add_argument("--json", help="JSON for configure p4", type=str, action="store", required=True)
args = parser.parse_args()

def main():
	BackgroundList = []
	P4SwitchList = []
	HostList = []
	net = Mininet(controller = None, link = TCLink)
	Controller = RemoteController( 'Controller', ip='127.0.0.1', port=6633)
	
	for i in range(0,2,1):
		P4SwitchList.append(net.addSwitch("s%02d"%(i+1), cls = P4RuntimeSwitch, sw_path=args.bmv2, json_path=args.json, cpu_port=255))
	for i in range(0,2,1):
		HostList.append(net.addHost("h%02d"%(i+1), cls=P4Host, ip = "192.168.1.%d/24"%(i+11), mac = "00:04:00:00:00:%d"%(i+1)))
	
	# Topology
	net.addLink(HostList[0], P4SwitchList[0], bw=1000)
	net.addLink(HostList[1], P4SwitchList[1], bw=1000)
	net.addLink(P4SwitchList[0], P4SwitchList[1], bw=1000)

	net.start()
	CLI(net)
	net.stop()

if __name__ == "__main__":
	setLogLevel( "info" )
	main()
