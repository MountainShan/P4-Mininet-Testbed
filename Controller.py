#!/usr/bin/env python2
import argparse
import grpc
import os
import sys
from time import sleep
# GRPC client
import p4_control.p4_runtime_lib.bmv2
from p4_control.p4_runtime_lib.switch import ShutdownAllSwitchConnections
import p4_control.p4_runtime_lib.helper

# Thrift client
import p4_control.bm_runtime_lib.bm_runtime


class P4_Controller:
    def __init__ (self):
        self.switches = {}
        self.thread_flag = True
        self.p4info_helper = None

    def _write_rules(self, switch, ingress_port, source, target, vlan_id, output):
        try:
            table_entry = self.p4info_helper.buildTableEntry(
                table_name="MyIngress.vlan_forwarding",
                match_fields={ "standard_metadata.ingress_port": ingress_port, "hdr.ipv4.srcAddr": source, "hdr.ipv4.dstAddr": target, "hdr.vlan.id": vlan_id },
                action_name="MyIngress.do_vlan_forwarding",
                action_params={ "port": output })
            switch.WriteTableEntry(table_entry)
        except:
            pass
   
    def writeCloneSessionRules(self, switch, clone_session_id, port):
        try:
            clone_entry = self.p4info_helper.buildCloneSessionEntry(clone_session_id=clone_session_id,port=port)
            switch.WriteCloneSessionEntry(clone_entry)
        except:
            pass

    def printGrpcError(self, error_msg):
        print "gRPC Error:", error_msg.details(),
        status_code = error_msg.code()
        print "(%s)" % status_code.name,
        traceback = sys.exc_info()[2]
        print "[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno)

    

    def arp_packet_handler(self, response):
        payload = response.packet.payload
        cpu_header = CPU_Header(payload[:14])
        msg = Ether(payload[14:])
        cpu_header.port = self.host_list[msg[ARP].pdst]['port']
        cpu_header.cpu_type = 0x11
        if ((msg[ARP].pdst not in self.host_list and msg[ARP].pdst not in self.background_list)):
            return
        packet = cpu_header.Deparser(payload[14:])
        self.switches[self.host_list[msg[ARP].pdst]['device_id']]["GRPC"].PacketOut(packet)
        return 

    def packet_in_handler(self, sw_id):
        while (self.thread_flag):
            response = self.switches[sw_id]["GRPC"].PacketIn()
	    if (response):
	    	# Packet process
	    	pass
        
    def main(self, p4info_file_path, bmv2_file_path):
        self.p4info_helper = p4_control.p4_runtime_lib.helper.P4InfoHelper(p4info_file_path)
        try:
            for sw in range(0,10,1):
                grpc_client = p4_control.p4_runtime_lib.bmv2.Bmv2SwitchConnection(name='s%02d'%(sw+1),address='127.0.0.1:%d'%(50051+sw),device_id=sw,proto_dump_file='None')
                grpc_client.MasterArbitrationUpdate()
                grpc_client.SetForwardingPipelineConfig(p4info=self.p4info_helper.p4info, bmv2_json_file_path=bmv2_file_path)
                thrift_client = p4_control.bm_runtime_lib.bm_runtime.bm_connection(address="127.0.0.1:%d"%(9090+sw), json=bmv2_file_path)
                self.switches.setdefault(sw, {"GRPC":grpc_client, "Thrift":thrift_client})
            

	    # Default Entries
            threads = []
            print(" >>> Start monitoring ports and flows. ")
            for sw_id in self.switches:
                threads.append(threading.Thread(target=self.packet_in_header, kwargs={"sw_id":sw_id}))
                threads[-1].start()
            while(True):
            	# Waiting for packet in event
                sleep(1)
        
        except KeyboardInterrupt:
            print " Shutting down."
            self.thread_flag = False
        except grpc.RpcError as e:
            self.printGrpcError(e)
        finally:
            ShutdownAllSwitchConnections()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--target', help='target file of p4', type=str, action="store", required=True)
    args = parser.parse_args()

    P4Controller = P4_Controller()
    target_p4info = "./build/"+args.target+".p4.p4info.txt"
    target_p4json = "./build/"+args.target+".json"
    P4Controller.main(target_p4info,target_p4json)
