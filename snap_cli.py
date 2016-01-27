#!/usr/bin/python

import sys
import socket
from snap_global import Global_CmdLine
from snap_interface import Interface_CmdLine
from cmd import Cmd
import readline
import rlcompleter
from flexswitch import FlexSwitch


_SHOW_BGP_NEIGH={'neighbors':['detail']}
_SHOW_BGP={'bgp':[_SHOW_BGP_NEIGH,'summary']}
_SHOW_ROUTE={'route':['summary', 'interface', 'bgp', 'ospf', 'static']}
_SHOW_BASE = {'ip':[_SHOW_BGP,_SHOW_ROUTE,'interface','arp'],'version':[''], 'inventory':['detail'], 'interface':['']}

_IP_HELP = {'summary':'Display summarized information of BGP state',
			'interface':'Display IP related interface information',
			'route':'Display routing information',
			'arp':'Display ARP table and statistics'
					}
_SHOW_HELP = {'version':'Show the software version',
			'interface':'Display IP related interface information',
			'inventory':'Show physical inventory',
			'ip':'Display IP information'
					}
_BGP_HELP = {'summary':'Display summarized information of BGP state',
			'neighbors':'Display all configured BGP neighbors',
					}	
_BGP_NEIGH = {'detail':'Display detailed information for BGP neighbors'
					}
_INVENT_HELP = {'detail':'Display detailed information for device inventory '
					}
_ROUTE_HELP = 	{'summary':'Display summarized information of routes',
				'interface':'Display routes with this output interface only',
				'bgp':'Display routes owned by bgp',
				'ospf':'Display routes owned by ospf',
				'static':'Display routes owned by static'
					}	
								
_COMMAND_HELP = {'ip':_IP_HELP,
				'show':_SHOW_HELP, 
				'bgp':_BGP_HELP,
				'route':_ROUTE_HELP,
				'bgp_neigh':_BGP_NEIGH,
				'inventory':_INVENT_HELP
				}
    
USING_READLINE = True
try:
    # For platforms without readline support go visit ...
    # http://pypi.python.org/pypi/readline/
    import readline
    import rlcompleter
    if 'libedit' in readline.__doc__:
    	readline.parse_and_bind("bind ^I rl_complete")
    else:
    	readline.parse_and_bind("tab: complete")    	
except:
    try:
        # For Windows readline support go visit ...
        # https://launchpad.net/pyreadline
        import pyreadline
    except:
        USING_READLINE = False

class FlexSwitch_info():

   def displayBGPPeers(self):
   		   switch_ip='10.1.10.240'
		   self.swtch = FlexSwitch(switch_ip,8080)
		   sessionState=  {  0: "Idle",
							 1: "Connect",
							 2: "Active",
							 3: "OpenSent",
							 4: "OpenConfirm",
							 5: "Established"
						   } 
	
		   peers = self.swtch.getObjects('BGPNeighborStates')
		   if len(peers)>=0: 
			   print '---- BGP Peers ----'
			   print 'Neighbor   LocalAS   PeerAS     State      RxNotifications    RxUpdates   TxNotifications TxUpdates'
		   for pr in peers:
			   print '%s    %s      %s     %s       %s              %s              %s           %s' %(pr['NeighborAddress'],
																				  pr['LocalAS'],
																				  pr['PeerAS'],
																				  sessionState[int(pr['SessionState'] -1)],
																				  pr['Messages']['Received']['Notification'],
																				  pr['Messages']['Received']['Update'],
																				  pr['Messages']['Sent']['Notification'],
																				  pr['Messages']['Sent']['Update'])


   def displayRoutes(self):
     	switch_ip='10.1.10.240'
     	self.swtch = FlexSwitch(switch_ip,8080)
     	routes = self.swtch.getObjects('IPV4Routes')
     	if len(routes)>=0:
     	    print '---- Routes ----'
     	    print 'Network            Mask         NextHop         Cost       Protocol   IfType IfIndex'
     	for rt in routes:
     	    print '%s %s %s %4d   %9s    %5s   %4s' %(rt['DestinationNw'].ljust(15), 
     	                                                    rt['NetworkMask'].ljust(15),
     	                                                    rt['NextHopIp'].ljust(15), 
     	                                                    rt['Cost'], 
     	                                                    rt['Protocol'], 
     	                                                    rt['OutgoingIntfType'], 
     	                                                    rt['OutgoingInterface'])
   def displayARPEntries(self):
     	switch_ip='10.1.10.240'
     	self.swtch = FlexSwitch(switch_ip,8080)
        arps = self.swtch.getObjects('ArpEntrys')
        if len(arps)>=0:
            print '---- ARPS ----'
            print 'IP Address	MacAddress   	    TimeRemaining  	Vlan 	  Intf'
        for d in arps:
            print  '%s	%s    %s	 %s	%s' %(d['IpAddr'],
						d['MacAddr'],
						d['ExpiryTimeLeft'],
						d['Vlan'],
						d['Intf'])

class CmdLine(Cmd):
    """
    Help may be requested at any point in a command by entering
    a question mark '?'.  If nothing matches, the help list will
    be empty and you must backup until entering a '?' shows the
    available options.
    Two styles of help are provided:
    1. Full help is available when you are ready to enter a
       command argument (e.g. 'show ?') and describes each possible
       argument.
    2. Partial help is provided when an abbreviated argument is entered
       and you want to know what arguments match the input
       (e.g. 'show pr?'.)
    """ 
    def __init__(self):
        Cmd.__init__(self)
        if not USING_READLINE:
            self.completekey = None
        self.prompt = socket.gethostname()+"#"
        self.intro = "FlexSwitch Console Version 1.0"
    def default(self, line):
        cmd, arg, line = self.parseline(line)
        cmds = self.completenames(cmd)
        #print cmds, arg
        num_cmds = len(cmds)
        if num_cmds == 1:
        	print arg
        	getattr(self, 'do_'+cmds[0])(arg)
        elif num_cmds > 1:
            sys.stdout.write('%% Ambiguous command:\t"%s"\n' % cmd)
        else:
            sys.stdout.write('% Unrecognized command\n')
 

    def emptyline(self):
        pass

    def do_help(self, arg):
        doc_strings = [ (i[3:], getattr(self, i).__doc__)
            for i in dir(self) if i.startswith('do_') ]
        doc_strings = [ '  %s\t%s\n' % (i, j)
            for i, j in doc_strings if j is not None ]
        sys.stdout.write('%s\n' % ''.join(doc_strings))
 
    def do_configure(self, args):
		" Global configuration mode "
		gconf = Global_CmdLine()
		gconf.prompt = self.prompt[:-1] + "(config)#"
		gconf.cmdloop()
		
    
    
    def do_show(self, arg):
        " Show running system information "
        fs_info = FlexSwitch_info()
        if "?" in self.lastcmd:
        	return 
        if 'ip' in arg:
        	if 'bgp' in arg:
        		#print bgp table
        		if 'neighbors' in arg:
        			#print BGP neighbors
        			sys.stdout.write("neighbor\n")
        		elif 'summary' in arg:
        			fs_info.displayBGPPeers()
        	elif 'route' in arg:
        		fs_info.displayRoutes()
        	elif 'arp' in arg:
        		fs_info.displayARPEntries()
        		
        else:
        	sys.stdout.write('% Incomplete command\n')
	    	
    def complete_show(self, text, line, begidx, endidx):
    	lines=line.strip()
    	list=[]
    	#print lines
    	#print line.endswitch("show")
    	#if lines.endswitch("show"):
    	if 'show' in lines:
    		if 'ip' in lines:
    			if 'bgp' in lines:
	    			if 'neighbors' in lines:
	    				for keys in _SHOW_BGP.get('bgp'):
	    					if type(keys) is dict:
	    						for var in keys:
	    							list.append(var)
	    			
	    				return [i for i in list if i.startswith(text)]
	    				
	    			elif 'summary' in lines:
	    				return
	    			else:
	    				for keys in _SHOW_BGP.get('bgp'):
	    					if type(keys) is dict:
	    						for var in keys:
	    							list.append(var)
	    					else:
   								list.append(keys)
	    				return [i for i in list if i.startswith(text)]
	    		elif 'route' in lines:
	    			if 'summary' in lines:
	    				for keys in _SHOW_ROUTE.get('route'):
	    					list.append(keys)
	    				return [i for i in list if i.startswith(text)]
	    			
	    			else:
	    				for keys in _SHOW_ROUTE.get('route'):
	    					list.append(keys)
	    				return [i for i in list if i.startswith(text)]
    			else:
    				for keys in _SHOW_BASE.get('ip'):
    					if type(keys) is dict:
    						for var in keys:
    							list.append(var)    				
    					else:
    						list.append(keys)			
    				return [i for i in list if i.startswith(text)] 
    		else:
    			return [i for i in _SHOW_BASE if i.startswith(text)]
    				
    def do_quit(self, args):
		" Quiting FlexSwitch CLI"
		sys.stdout.write('Quiting Shell\n')
		sys.exit(0)	
		
    def do_exit(self, args):
		" Quiting FlexSwitch CLI"
		sys.stdout.write('Exiting Shell\n')
		sys.exit(0)	
		
    def do_end(self, args):
        " Return to enable  mode"
    	return
    	
    def do_shell(self, args):
       sys.stdout.write("")
        
    def precmd(self, line):
        if line.strip() == 'help':
            sys.stdout.write('%s\n' % self.__doc__)
            return ''
        cmd, arg, line = self.parseline(line)
        if line.strip() == '?':
            cmds = self.completenames(cmd)
            if cmds:
            	#sys.stdout.write('%s\n' % self.__doc__)
                self.columnize(cmds)
                sys.stdout.write('\n')
            return ''
        elif line.endswith('?'):
        	if 'show' in line:
    			if 'ip' in line:
    				if 'bgp' in line:
	    				if 'neighbors' in line:
	    					sys.stdout.write('   <CR>\n')
	    					for keys in _COMMAND_HELP.get('bgp_neigh'):
	    						sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('bgp_neigh').get(keys)) ) 
	    					return line
	    				elif 'summary' in line:
	    					sys.stdout.write('   <CR>\n')	    					
	    					return line
	    				else:
	    					sys.stdout.write('   <CR>\n')
	    					for keys in _COMMAND_HELP.get('bgp'):
	    						sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('bgp').get(keys)) ) 	    					
    						return line
	    			elif 'route' in line:
	    				sys.stdout.write('   <CR>\n')
	    				for keys in _COMMAND_HELP.get('route'):
	    					sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route').get(keys)) ) 	    					
    					return line
	    			else:
	    				for keys in _COMMAND_HELP.get('ip'):
	    					sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('ip').get(keys)) )
    					return line
    			elif 'interface' in line:
    				sys.stdout.write('   <CR>\n')
    				return line
    			elif 'inventory' in line:
    				sys.stdout.write('   <CR>\n')
    				for keys in _COMMAND_HELP.get('inventory'):
	    				sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('inventory').get(keys)) )
    				return line
    			else:
    				for keys in _COMMAND_HELP.get('show'):
	    				sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('show').get(keys)) )
    				return line
        return line            
    	
# *** MAIN LOOP ***
if __name__ == '__main__':
    cmdLine = CmdLine()
    cmdLine.cmdloop()
