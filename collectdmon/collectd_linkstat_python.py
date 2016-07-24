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

    def parse_speed(self, port_cfg):
        return port_cfg["Object"]["Speed"]

    def get_portconfigs(self, switch_ip):
	swtch = FlexSwitch (switch_ip, 8080)
	portscfg = swtch.getAllPorts()
	return portscfg
	
    def get_portstats(self, switch_ip):
        swtch = FlexSwitch (switch_ip, 8080)  # Instantiate object to talk to flexSwitch
	ports = swtch.getAllPortStates()
        return ports
	
    def parse_ports(self, port_object):
	return port_object["Object"]["IfOutOctets"]

class PortMon(object):
    def __init__(self):
        self.plugin_name = 'collectd_linkstat_python'
        self.portstat_path = '/usr/bin/linkstat'
     
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
        """
        Collectd read callback
        """
        print("Read callback called")
        portstat = PortStat()
        portout = portstat.get_portstats("10.1.10.242")
        portcfg = portstat.get_portconfigs("10.1.10.242")
	pmap = {}
	for  pcfg in portcfg:
            pmap[json.dumps(pcfg["Object"]["IntfRef"])] = portstat.parse_speed(pcfg)


        index = 0
        for port_object in portout:
            portout = portstat.parse_ports(port_object)
            port_name = json.dumps(port_object["Object"]["IntfRef"])
            portspeed = pmap[port_name]
            modspeed = (portout/10**6) * 8
            linkutil = (modspeed/portspeed) * 100
            print("port speed %s : %s"%(port_name, str(linkutil)))
            portmon.sendToCollect('gauge', port_name, str(linkutil))
            index = index + 1


if __name__ == '__main__':
     portstat = PortStat()
     portmon = PortMon()
     portout = portstat.get_portstats("10.1.10.242")
     portcfg = portstat.get_portconfigs("10.1.10.242")
     index = 0
     #parse port names
     pmap = {}
     for  pcfg in portcfg:
	pmap[json.dumps(pcfg["Object"]["IntfRef"])] = portstat.parse_speed(pcfg)

     for port_object in portout:
         portout = portstat.parse_ports(port_object)
	 port_name = json.dumps(port_object["Object"]["IntfRef"])
         portspeed = pmap[port_name]
         modspeed = (portout/10**6) * 8
         linkutil = (modspeed/portspeed) * 100 
	 print("port speed %s : %s"%(port_name, str(linkutil)))
         portmon.sendToCollect('gauge', port_name, str(linkutil))
     sys.exit(0)
else:
    import collectd

    portmon = PortMon()

    # Register callbacks
  
    collectd.register_init(portmon.init_callback) 
    collectd.register_config(portmon.configure_callback)
    collectd.register_read(portmon.read_callback)
