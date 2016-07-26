#!/usr/bin/env python
import os
import signal
import string
import subprocess
import sys
import json
sys.path.append(os.path.abspath('../../py'))
from flexswitchV2 import FlexSwitch

class PortStat(object):
    def __init__(self):
	print("Start monitoring portstat")
	
    def get_portstats(self, stwitch_ip):
        swtch = FlexSwitch (stwitch_ip, 8080)  # Instantiate object to talk to flexSwitch
	ports = swtch.getAllPortStates()
        return ports
	
    def parse_ports(self, port_object):
	return json.dumps(port_object["Object"]["IfOutOctets"])	

class PortMon(object):
    def __init__(self):
        self.plugin_name = 'collectd-portstat-python'
        self.portstat_path = '/usr/bin/portstat'
     
    def init_callback(self):
	print("Nothing to be done here now ")
 
    def configure_callback(self, conf):
	for node in conf.children:
            val = str(node.values[0]) 
            print(" config  %s"%val)
		
    def sendToCollect(self, val_type, type_instance, value):
        val = collectd.Values()
        val.plugin = self.plugin_name
        val.type = val_type
        
        val.type_instance = type_instance
        val.values = [value, ]
        val.meta={'0': True}
        val.dispatch()
		    
    def read_callback(self):
        print("Read callback called")
        portstat = PortStat()
        ports = portstat.get_portstats("localhost")
	for port_object in ports:
            stat = portstat.parse_ports(port_object)
	    port_name = port_object["Object"]["IntfRef"]
	    print("%s : %s"%(port_name, stat))
            self.sendToCollect('derive', port_name, stat) 


if __name__ == '__main__':
     portstat = PortStat()
     portmon = PortMon()
     ports = portstat.get_portstats("localhost")
     for port_object in ports:
         stat = portstat.parse_ports(port_object)
	 port_name = json.dumps(port_object["Object"]["IntfRef"])
	 print("%s : %s"%(port_name, stat))
         portmon.sendToCollect('derive', port_name, stat)

     sys.exit(0)
else:
    import collectd

    portmon = PortMon()

    # Register callbacks
  
    collectd.register_init(portmon.init_callback) 
    collectd.register_config(portmon.configure_callback)
    collectd.register_read(portmon.read_callback)
