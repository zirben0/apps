#!/usr/bin/env python
import os
import signal
import string
import subprocess
import sys
import json
sys.path.append(os.path.abspath('../../py'))
from flexswitchV2 import FlexSwitch

class BufferStat(object):
    def __init__(self):
	print("Start monitoring bufferstat")
	
    def get_bufferstats(self, stwitch_ip):
        swtch = FlexSwitch (stwitch_ip, 8080)  # Instantiate object to talk to flexSwitch
	buffers = swtch.getAllBufferStatStates()
        return buffers
	
    def parse_buffers(self, port_object):
	return json.dumps(port_object["Object"]["PortPoolBufferStat"])	

class BufferMon(object):
    def __init__(self):
        self.plugin_name = 'collectd-bufferstat-python'
        self.bufferstat_path = '/usr/bin/bufferstat'
     
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
        portstat = BufferStat()
        ports = portstat.get_bufferstats("localhost")
	for port_object in ports:
            stat = portstat.parse_buffers(port_object)
	    port_name = port_object["Object"]["IntfRef"]
	    print("%s : %s"%(port_name, stat))
            self.sendToCollect('gauge', port_name, stat) 


if __name__ == '__main__':
     portstat = BufferStat()
     portmon = BufferMon()
     ports = portstat.get_bufferstats("localhost")
     for port_object in ports:
         stat = portstat.parse_buffers(port_object)
	 port_name = json.dumps(port_object["Object"]["IntfRef"])
	 print("%s : %s"%(port_name, stat))
         portmon.sendToCollect('gauge', port_name, stat)

     sys.exit(0)
else:
    import collectd

    portmon = BufferMon()

    # Register callbacks
  
    collectd.register_init(portmon.init_callback) 
    collectd.register_config(portmon.configure_callback)
    collectd.register_read(portmon.read_callback)
