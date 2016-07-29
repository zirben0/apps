#!/usr/bin/env python
import os
import signal
import string
import subprocess
import sys
import datetime
import json
try:
    from flexswitchV2 import FlexSwitch
except:
    sys.path.append('/opt/flexswitch/sdk/py/')
    from flexswitchV2 import FlexSwitch

class PortStat(object):
    def __init__(self):
	print("Start monitoring portstat in bps")
	
    def get_portstats(self, stwitch_ip):
        swtch = FlexSwitch (stwitch_ip, 8080)  # Instantiate object to talk to flexSwitch
	ports = swtch.getAllPortStates()
        return ports
	
    def parse_ports(self, port_object):
        return json.dumps(port_object["Object"]["IfOutOctets"] * 8)

    def parse_inPorts(self, port_object):
        return json.dumps(port_object["object"]["IfInOctets"] * 8)

class PortMon(object):
    def __init__(self):
        self.plugin_name = 'collectd-bpsstat-python'
        self.portstat_path = '/usr/bin/bpsstat'
     
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

    def collectStats(self, portstat, port_object):
        stat = portstat.parse_ports(port_object)
        port_name = port_object["Object"]["IntfRef"]

        outPn = "outBPS"
        print("%s : %s"%(port_name, stat))
        self.sendToCollect('derive', port_name+outPn, stat) 
        
        inPn = "inBPS"
        inP = portstat.parse_ports(port_object)  
        self.sendToCollect('derive', port_name+inPn, inP)

    def read_callback(self):
       
        print("Read callback called")
        portstat = PortStat()
        ports = portstat.get_portstats("localhost")
	for port_object in ports:
            self.collectStats(portstat, port_object)


if __name__ == '__main__':
     portstat = PortStat()
     portmon = PortMon()
     ports = portstat.get_portstats("localhost")
     for port_object in ports:
         portmon.collectStats(portstat, port_object)

     sys.exit(0)
else:
    import collectd

    portmon = PortMon()

    # Register callbacks
  
    collectd.register_init(portmon.init_callback) 
    collectd.register_config(portmon.configure_callback)
    collectd.register_read(portmon.read_callback)
