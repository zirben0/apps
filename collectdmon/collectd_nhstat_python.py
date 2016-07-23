#!/usr/bin/env python
import os
import signal
import string
import subprocess
import sys
import json
sys.path.append(os.path.abspath('../../py'))
from flexswitchV2 import FlexSwitch

class nhStat(object):
    def __init__(self):
	print("Collect nh stats init called.")
	
    def get_nhstats(self, stwitch_ip):
        swtch = FlexSwitch (stwitch_ip, 8080)  # Instantiate object to talk to flexSwitch
	nhs = swtch.getAllIPv4RouteStates()
        return nhs
	
    def parse_nhs(self, nh_object):
        nexthoplist = nh_object["Object"]["NextHopList"]
	nhcount = 0
	for nh in nexthoplist:  #Get nh count for the prefix
	    nhcount = nhcount + 1

	return str(nhcount)	

class nhMon(object):
    def __init__(self):
        self.plugin_name = 'collectd_nhstat_python'
        self.nhstat_path = '/usr/bin/nhstat'
     
    def init_callback(self):
	print("Nothing to be done here now ")
 
    def configure_callback(self, conf):
	for node in conf.children:
            val = str(node.values[0]) 
            print(" config  %s"%val)
		
    def sendToCollector(self, val_type, type_instance, value):
        val = collectd.Values()
        val.plugin = self.plugin_name
        val.type = val_type
        
        val.type_instance = type_instance
        val.values = [value, ]
        val.meta={'0': True}
        val.dispatch()
		    
    def read_callback(self):
        """
        Collectd read callback
        """
        print("Read callback called")
        nhstat = nhStat()
        nhs = nhstat.get_nhstats("localhost")
	for nh_object in nhs:
            stat = nhstat.parse_nhs(nh_object)
	    nh_name = nh_object["Object"]["DestinationNw"]
	    print("%s : %s"%(nh_name, stat))
            self.sendToCollector('gauge', nh_name, stat) 


if __name__ == '__main__':
     nhstat = nhStat()
     nhmon = nhMon()
     nhs = nhstat.get_nhstats("localhost")
     for nh_object in nhs:
         stat = nhstat.parse_nhs(nh_object)
	 nh_name = json.dumps(nh_object["Object"]["DestinationNw"])
	 print("%s : %s"%(nh_name, stat))
         nhmon.sendToCollector('gauge', nh_name, stat)

     sys.exit(0)
else:
    import collectd

    nhmon = nhMon()

    # Register callbacks
  
    collectd.register_init(nhmon.init_callback) 
    collectd.register_config(nhmon.configure_callback)
    collectd.register_read(nhmon.read_callback)
