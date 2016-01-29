#!/usr/bin/python

import sys, getopt, socket
from snap_global import Global_CmdLine
#from snap_interface import Interface_CmdLine
from cmd import Cmd
import readline
import rlcompleter
from flexswitch import FlexSwitch


#### SHOW COMMAND AUTOCOMPLETION DICT ##########
_SHOW_BGP_NEIGH={'neighbors':['detail']}
_SHOW_BGP={'bgp':[_SHOW_BGP_NEIGH,'summary']}
_SHOW_OSPF_NEIGH={'neighbors':['detail']}
_SHOW_OSPF={'ospf':[_SHOW_BGP_NEIGH,'interface']}
_SHOW_ROUTE={'route':['summary', 'interface', 'bgp', 'ospf', 'static']
			}
_SHOW_PCHANNEL={'summary':['interface'], 'load-balance':[''], 'interface':['detail']
			}
_SHOW_BASE = {'ip':[_SHOW_BGP,_SHOW_ROUTE,_SHOW_OSPF,'interface','arp'],
			'version':[''], 'inventory':['detail'], 'interface':['counters'],
			'port-channel':_SHOW_PCHANNEL,'bfd':['interface','summary']
			}

#### HELP COMMAND TEXT FROM '?' ##########
_IP_HELP = {'interface':'Display IP related interface information',
			'route':'Display routing information',
			'arp  ':'Display ARP table and statistics',
			'bgp':'Display BGP status and configuration'
					}
_SHOW_HELP = {'version':'Show the software version',
			'interface':'Display IP related interface information',
			'inventory':'Show physical inventory',
			'ip':'Display IP information'
					}
_BGP_HELP = {'summary':'Display summarized information of BGP state',
			'neighbors':'Display all configured BGP neighbors',
					}	
_BGP_NEIGH_HELP = {'detail':'Display detailed information for BGP neighbors'
					}
_INVENT_HELP = {'detail':'Display detailed information for device inventory '
					}
_ROUTE_HELP = 	{'summary':'Display summarized information of routes',
				'interface':'Display routes with this output interface only',
				'bgp  ':'Display routes owned by bgp',
				'ospf ':'Display routes owned by ospf',
				'static':'Display routes owned by static'
					}	
								
_COMMAND_HELP = {'ip':_IP_HELP,
				'show':_SHOW_HELP, 
				'bgp':_BGP_HELP,
				'route':_ROUTE_HELP,
				'bgp_neigh':_BGP_NEIGH_HELP,
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

   def __init__(self,switch_ip):
   		self.switch_ip=switch_ip
   		self.swtch = FlexSwitch(self.switch_ip,8080)
   		
   def displayBGPPeers(self):	   
		   sessionState=  {  0: "Idle",
							 1: "Connect",
							 2: "Active",
							 3: "OpenSent",
							 4: "OpenConfirm",
							 5: "Established"
						   } 
	
		   peers = self.swtch.getObjects('BGPNeighborStates')
		   if len(peers)>=0: 
			   print '\n'
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

		   print "\n"
			   
   def displayRoutes(self):
     	routes = self.swtch.getObjects('IPV4Routes')
     	if len(routes)>=0:
     	    print '\n'
     	    print 'Network            Mask         NextHop         Cost       Protocol   IfType IfIndex'
     	for rt in routes:
     	    print '%s %s %s %4d   %9s    %5s   %4s' %(rt['DestinationNw'].ljust(15), 
     	                                                    rt['NetworkMask'].ljust(15),
     	                                                    rt['NextHopIp'].ljust(15), 
     	                                                    rt['Cost'], 
     	                                                    rt['Protocol'], 
     	                                                    rt['OutgoingIntfType'], 
     	                                                    rt['OutgoingInterface'])
        print "\n"

   def displayARPEntries(self):
        arps = self.swtch.getObjects('ArpEntrys')
        if len(arps)>=0:
            print '\n'
            print 'IP Address	MacAddress   	    TimeRemaining  	Vlan 	  Intf'
        for d in arps:
            print  '%s	%s    %s	 %s	%s' %(d['IpAddr'],
						d['MacAddr'],
						d['ExpiryTimeLeft'],
						d['Vlan'],
						d['Intf'])
        print "\n"

   def displayPortObjects(self):
        ports = self.swtch.getObjects('PortStates')
        if len(ports):
            print '\n'
            print 'Port         InOctets   InUcastPkts   InDiscards  InErrors     InUnknownProtos   OutOctets OutUcastPkts   OutDiscards   OutErrors'
        for d in ports:
            if d['IfIndex'] == 0:
        		continue
            #if sum(d['PortStats']):
            print '%s  %8d %10d   %10d    %8d   %15d   %9d   %12d   %11d   %11d' %("fpPort-"+str(d['IfIndex']),
                                                                d['PortStats'][0],
                                                                d['PortStats'][1],
                                                                d['PortStats'][2],
                                                                d['PortStats'][3],
                                                                d['PortStats'][4],
                                                                d['PortStats'][5],
                                                                d['PortStats'][6],
                                                                d['PortStats'][7],
                                                                d['PortStats'][8])
        print "\n"
   def displayCPUPortObjects(self):
        ports = self.swtch.getObjects('PortStates')
        if len(ports):
            print '\n'
            print 'Port         InOctets   InUcastPkts   InDiscards  InErrors     InUnknownProtos   OutOctets OutUcastPkts   OutDiscards   OutErrors'
        for d in ports:
            if d['IfIndex'] == 0:
            	print '%s  %8d %10d   %10d    %8d   %15d   %9d   %12d   %11d   %11d' %("fpPort-"+str(d['IfIndex']),
                                                                d['PortStats'][0],
                                                                d['PortStats'][1],
                                                                d['PortStats'][2],
                                                                d['PortStats'][3],
                                                                d['PortStats'][4],
                                                                d['PortStats'][5],
                                                                d['PortStats'][6],
                                                                d['PortStats'][7],
                                                                d['PortStats'][8])
        print "\n"

   def verifyDRElectionResult(self):
        ospfIntfs = self.swtch.getObjects('OspfIfEntryStates')
        print '\n'
        #self.assertNotEqual(len(ospfIntfs) != 0)
        if len(ospfIntfs)>=0:
            print 'IfAddr IfIndex  State  DR-RouterId DR-IpAddr BDR-RouterI BDR-IpAddr NumEvents LSACount LSACksum'

        for d in ospfIntfs:
            if sum(d['ospfIntfs']):
                print '%3s  %3d %10s   %10s    %8s   %15s   %9s   %12s   %11s   %11s' %( d['IfIpAddressKey'],
                                                                                        d['AddressLessIfKey'],
                                                                                        d['IfStat'],
                                                                                        d['IfDesignatedRoute'],
                                                                                        d['IfBackupDesignatedRoute'],
                                                                                        d['IfEvent'],
                                                                                        d['IfLsaCoun'],
                                                                                        d['IfLsaCksumSu'],
                                                                                        d['IfDesignatedRouterI'],
                                                                                        d['IfBackupDesignatedRouterI'])
        print "\n"            
   def getVlanInfo (self, vlanId):
        for vlan in self.swtch.getObjects ('VlanStates'):
            print vlan 
            if vlan['VlanId'] == vlanId:
                print int(vlan['IfIndex'])

   def getLagMembers(self):
      members = self.swtch.getObjects('AggregationLacpMemberStateCounterss')
      print '\n---- LACP Members----'
      if len(members):
   	   for d in members:
   		   print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n'
   		   print 'name: ' + d['NameKey'] + ' interface: ' + d['Interface']
   		   print 'enabled: %s' % d['Enabled']
   		   print 'lagtype: ' + ('LACP' if not d['LagType'] else 'STATIC')
   		   print 'operkey: %s' % d['OperKey']
   		   print 'mode: ' + ('ACTIVE' if not d['LacpMode'] else 'PASSIVE')
   		   print 'interval: %s' % (('SLOW' if d['Interval'] else 'FAST'))
   		   print 'system:\n'
   		   print '\tsystemmac: %s' % d['SystemIdMac']
   		   print '\tsysteprio: %s' % d['SystemPriority']
   		   print '\tsystemId: %s' % d['SystemId']
   		   print 'actor:'
   		   stateStr = '\tstate: '
   		   for s in ('Activity', 'Timeout', 'Aggregatable', 'Synchronization', 'Collecting', 'Distributing'):
   			   if s == 'Synchronization' and not d[s]:
   				   stateStr += s + ', '
   			   elif s == 'Activity' and not d[s]:
   				   stateStr += s + ', '
   			   elif s in ('Activity', 'Synchronization'):
   				   continue
   			   elif d[s]:
   				   stateStr += s + ', '
   		   print stateStr.rstrip(',')
   
   		   print '\tstats:'
   		   for s in ('LacpInPkts', 'LacpOutPkts', 'LacpRxErrors', 'LacpTxErrors', 'LacpUnknownErrors', 'LacpErrors', 'LampInPdu', 'LampOutPdu', 'LampInResponsePdu', 'LampOutResponsePdu'):
   			   print '\t' + s, ': ', d[s]
   
   		   print 'partner:\n'
   		   print '\t' + 'key: %s' % d['PartnerKey']
   		   print '\t' + 'partnerid: ' + d['PartnerId']
   


   def getLagMembers_detail(self): 
      RxMachineStateDict = {
          0 : "RX_CURRENT",
          1 : "RX_EXPIRED",
          2 : "RX_DEFAULTED",
          3 : "RX_INITIALIZE",
          4 : "RX_LACP_DISABLED",
      	5 : "RX_PORT_DISABLE",
      }
      
      MuxMachineStateDict = {
          0 : "MUX_DETACHED",
          1 : "MUX_WAITING",
          2 : "MUX_ATTACHED",
          3 : "MUX_COLLECTING",
      	4 : "MUX_DISTRIBUTING",
          5 : "MUX_COLLECTING_DISTRIBUTING",
      }
      
      ChurnMachineStateDict = {
          0 : "CDM_NO_CHURN",
          1 : "CDM_CHURN",
      }
      members = self.swtch.getObjects('AggregationLacpMemberStateCounterss')
      print '\n---- LACP Members----'
      if len(members):
   	   for d in members:
   		   print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n'
   		   print 'name: ' + d['NameKey'] + ' interface: ' + d['Interface']
   		   print 'enabled: %s' % d['Enabled']
   		   print 'lagtype: ' + ('LACP' if not d['LagType'] else 'STATIC')
   		   print 'operkey: %s' % d['OperKey']
   		   print 'mode: ' + ('ACTIVE' if not d['LacpMode'] else 'PASSIVE')
   		   print 'interval: %s' % (('SLOW' if d['Interval'] else 'FAST'))
   		   print 'system:\n'
   		   print '\tsystemmac: %s' % d['SystemIdMac']
   		   print '\tsysteprio: %s' % d['SystemPriority']
   		   print '\tsystemId: %s' % d['SystemId']
   		   print 'actor:'
   		   stateStr = '\tstate: '
   		   for s in ('Activity', 'Timeout', 'Aggregatable', 'Synchronization', 'Collecting', 'Distributing'):
   			   if s == 'Synchronization' and not d[s]:
   				   stateStr += s + ', '
   			   elif s == 'Activity' and not d[s]:
   				   stateStr += s + ', '
   			   elif s in ('Activity', 'Synchronization'):
   				   continue
   			   elif d[s]:
   				   stateStr += s + ', '
   		   print stateStr.rstrip(',')
   
   		   print '\tstats:'
   		   for s in ('LacpInPkts', 'LacpOutPkts', 'LacpRxErrors', 'LacpTxErrors', 'LacpUnknownErrors', 'LacpErrors', 'LampInPdu', 'LampOutPdu', 'LampInResponsePdu', 'LampOutResponsePdu'):
   			   print '\t' + s, ': ', d[s]
   
   		   print 'partner:\n'
   		   print '\t' + 'key: %s' % d['PartnerKey']
   		   print '\t' + 'partnerid: ' + d['PartnerId']
   		   print 'debug:\n'
   		   try:
   			   print '\t' + 'debugId: %s' % d['DebugId']
   			   print '\t' + 'RxMachineState: %s' % RxMachineStateDict[d['RxMachine']]
   			   print '\t' + 'RxTime (rx pkt rcv): %s' % d['RxTime']
   			   print '\t' + 'MuxMachineState: %s' % MuxMachineStateDict[d['MuxMachine']]
   			   print '\t' + 'MuxReason: %s' % d['MuxReason']
   			   print '\t' + 'Actor Churn State: %s' % ChurnMachineStateDict[d['ActorChurnMachine']]
   			   print '\t' + 'Partner Churn State: %s' % ChurnMachineStateDict[d['PartnerChurnMachine']]
   			   print '\t' + 'Actor Churn Count: %s' % d['ActorChurnCount']
   			   print '\t' + 'Partner Churn Count: %s' % d['PartnerChurnCount']
   			   print '\t' + 'Actor Sync Transition Count: %s' % d['ActorSyncTransitionCount']
   			   print '\t' + 'Partner Sync Transition Count: %s' % d['PartnerSyncTransitionCount']
   			   print '\t' + 'Actor LAG ID change Count: %s' % d['ActorChangeCount']
   			   print '\t' + 'Partner LAG ID change Count: %s' % d['PartnerChangeCount']
   		   except Exception as e:
   			   print e      
   
   def getLagGroups(self):
      lagGroup = self.swtch.getObjects('AggregationLacpStates')
      print '\n'
      if len(lagGroup)>=0:
   	   print 'Name      Ifindex      LagType   Description      Enabled   MinLinks   Interval   Mode          SystemIdMac            SystemPriority    HASH'
   
   	   for d in lagGroup:
   		   print '%7s  %7s    %7s  %15s    %8s   %2s     %8s      %6s   %20s         %s              %s' %(d['NameKey'],
   														   d['Ifindex'],
   														   "LACP" if int(d['LagType']) == 0 else "STATIC",
   														   d['Description'],
   														   "Enabled" if bool(d['Enabled']) else "Disabled",
   														   d['MinLinks'],
   														   "FAST" if int(d['Interval']) == 0 else "SLOW",
   														   "ACTIVE" if int(d['LacpMode']) == 0 else "PASSIVE",
   														   d['SystemIdMac'],
   														   d['SystemPriority'],
   														   d['LagHash'])
                                                                                                        
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
    def __init__(self, switch_ip):
        Cmd.__init__(self)
        if not USING_READLINE:
            self.completekey = None
        self.prompt = socket.gethostname()+"#"
        try:
        	switch_name = socket.gethostbyname(switch_ip)
        except socket.gaierror:
        	switch_name = switch_ip
        self.intro = "FlexSwitch Console Version 1.0, Connected to: " + switch_name 
        self.fs_info = FlexSwitch_info(switch_ip)
		
    def cmdloop(self):
        try:
        	Cmd.cmdloop(self)
        except KeyboardInterrupt as e:
        	self.intro = '\n'
        	self.cmdloop()      
              
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
		gconf = Global_CmdLine(self,self.fs_info)
		gconf.prompt = self.prompt[:-1] + "(config)#"
		gconf.cmdloop()
		
    
    def do_show(self, arg):
        " Show running system information "
        if "?" in self.lastcmd:
        	return 
        args=arg.split()
        #print args[0], args[1]
        if len(args):
        	try:
        		if 'ip' in args[0]:
        			if 'bgp' in args[1]:
        				#print bgp table
        				if 'neighbors' in args[2]:
        					#print BGP neighbors
        					sys.stdout.write("neighbor\n")
        				elif 'summary' in args[2]:
        					self.fs_info.displayBGPPeers()
        				else:
        					sys.stdout.write("% Invalid command \n")	
        			elif 'route' in args[1]:
        				self.fs_info.displayRoutes()
        			elif 'arp' in args[1]:
        				self.fs_info.displayARPEntries()
        			elif 'ospf' in args[1]:
        				if 'interface' in args[2]:
        					self.fs_info.verifyDRElectionResult()
        				else:
        					sys.stdout.write("% Invalid command \n")
        			else:
        				sys.stdout.write("% Invalid command \n")
        		elif 'interface' in args[0]:
        			if 'counters' in args[1]:
        				if len(args) == 2:
        					self.fs_info.displayPortObjects()
        				else:
        					if 'cpu' in args[2]:
        						self.fs_info.displayCPUPortObjects()
        					else:
        						sys.stdout.write('% Invalid command\n')  
        			else:
        				sys.stdout.write("% Invalid command \n")	
        		elif 'vlan' in args[0]:
        			if len(args) >=2:
        				if 1 <= int(args[1]) <= 4094:
        					self.fs_info.getVlanInfo(args[1])
        				else:
        					sys.stdout.write("% Invalid command \n")
        			else:
        				sys.stdout.write('% Incomplete command\n')
        		elif 'port-channel' in args[0]:
        			if 'summary' in args[1]:
        				self.fs_info.getLagGroups()
        			elif 'interface' in args[1]:       				
        				if len(args) == 2:
        					self.fs_info.getLagMembers()
        				else:
        					if 'detail' in args[2]:
        						self.fs_info.getLagMembers_detail()
        					else:
        						sys.stdout.write('% Invalid command\n')     				
        			else:
        				sys.stdout.write('% Invalid command\n')
        		else:
        			sys.stdout.write('% Incomplete command\n')
        	except IndexError:
        		sys.stdout.write('% Incomplete command\n')
        		
        	except :
        		sys.stdout.write('% Loss connectivity to %s \n' % switch_name )
        else:
        	sys.stdout.write('% Incomplete command\n')

#Auto Completion for show commands in Enable mode	    	
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
	    					if keys in lines:
	    						continue
	    					else:
	    						list.append(keys)
	    				return [i for i in list if i.startswith(text)]
	    			
	    			else:
	    				for keys in _SHOW_ROUTE.get('route'):
	    					if keys in lines:
	    						continue
	    					else:
	    						list.append(keys)
	    				return [i for i in list if i.startswith(text)]
    			else:
    				for keys in _SHOW_BASE.get('ip'):
    					if type(keys) is dict:
    						for var in keys:
    							list.append(var)    				
    					else:
    						if keys in lines:
	    						continue
	    					else:
	    						list.append(keys)			
    				return [i for i in list if i.startswith(text)]
    				 
	    	elif 'port-channel' in lines:
	    		#print "goo"
	    		if 'summary' in lines:
	    			for keys in _SHOW_PCHANNEL.get('summary'):
	    				if keys in lines:
	    					continue
	    				else:
	    					list.append(keys)
	    			return [i for i in list if i.startswith(text)]
	    		elif 'load-balance' in lines:
	    			for keys in _SHOW_PCHANNEL.get('load-balance'):
	    				if keys in lines:
	    					continue
	    				else:
	    					list.append(keys)
	    			return [i for i in list if i.startswith(text)]	
	    		elif 'interface' in lines:
	    			for keys in _SHOW_PCHANNEL.get('interface'):
	    				if keys in lines:
	    					continue
	    				else:
	    					list.append(keys)
	    			return [i for i in list if i.startswith(text)]	 
	    			
	    		else:
	    			for keys in _SHOW_PCHANNEL:
	    				if keys in lines:
	    					continue
	    				else:
	    					if keys in lines:
	    						continue
	    					else:
	    						list.append(keys)
	    			return [i for i in list if i.startswith(text)]   		    			    		
    		elif 'interface' in lines:	
	    		return [i for i in _SHOW_BASE.get('interface') if i.startswith(text)]
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
       # cmd, arg, line = self.parseline(line)
        #if line.strip() == '?':
         #   cmds = self.completenames(cmd)
          #  if cmds:
            	#sys.stdout.write('%s\n' % self.__doc__)
           #     self.columnize(cmds)
            #    sys.stdout.write('\n')
            #return ''
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

def usage():
    usage = """
    -h --help		Prints Help
    -s --switch		FlexSwitch IP address (defaults to 127.0.0.1)
    """
    print(usage)
        	
# *** MAIN LOOP ***
if __name__ == '__main__':
    switch_ip='127.0.0.1'
	#Get Opts from User.  Set switch IP to connect, if not local. 
    try:
    	opts, args = getopt.getopt(sys.argv[1:], "hs:", ["help", "switch=",])
    	#if not opts:
        #               print('No options supplied')
        #               usage()
        #               sys.exit(2)
    except getopt.GetoptError as err:
    	# print help information and exit:
    	print(str(err)) # will print something like "option -a not recognized"
    	usage()
    	sys.exit(2)
    
    for opt,arg in opts:
    	if opt in ("-h","--help"):
    		usage()
    		sys.exit(2)
    	elif opt in ("-s","--switch"):
    		switch_ip = arg
    	else:
    		print ("Syntax Error")
    		usage()
    		sys.exit(2)	
    		
    cmdLine = CmdLine(switch_ip)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((switch_ip,8080))
    
    if result == 0:
    	cmdLine.cmdloop()
    else:
   		print "FlexSwitch not reachable, Please ensure daemon is up."  
   		sys.exit(2)
