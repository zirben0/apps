#!/usr/bin/env python
import os
import signal
import string
import subprocess
import sys
import json
sys.path.append(os.path.abspath('../../py'))
from flexswitchV2 import FlexSwitch

class BGPStat(object):
    def __init__(self):
	print("Collect bgp stats init called.")
	
    def get_BGPstats(self, stwitch_ip):
        swtch = FlexSwitch (stwitch_ip, 8080)  # Instantiate object to talk to flexSwitch
	bgps = swtch.getAllBGPNeighborStates()
        return bgps
	
    def parse_bgps(self, bgp_object):
	return json.dumps(bgp_object["Object"]["TotalPrefixes"])	

class BGPMon(object):
    def __init__(self):
        self.plugin_name = 'collectd_bgpstat_python'
        self.bgpstat_path = '/usr/bin/bgpstat'
     
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
        bgpstat = BGPStat()
        bgps = bgpstat.get_BGPstats("localhost")
	for bgp_object in bgps:
            stat = bgpstat.parse_bgps(bgp_object)
	    bgp_name = bgp_object["Object"]["NeighborAddress"]
	    print("%s : %s"%(bgp_name, stat))
            self.sendToCollector('gauge', bgp_name, stat) 


if __name__ == '__main__':
     bgpstat = BGPStat()
     bgpmon = BGPMon()
     bgps = bgpstat.get_BGPstats("localhost")
     for bgp_object in bgps:
         stat = bgpstat.parse_bgps(bgp_object)
	 bgp_name = json.dumps(bgp_object["Object"]["NeighborAddress"])
	 print("%s : %s"%(bgp_name, stat))
         bgpmon.sendToCollector('gauge', bgp_name, stat)

     sys.exit(0)
else:
    import collectd

    bgpmon = BGPMon()

    # Register callbacks
  
    collectd.register_init(bgpmon.init_callback) 
    collectd.register_config(bgpmon.configure_callback)
    collectd.register_read(bgpmon.read_callback)
