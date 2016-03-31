import sys, types, json
from flexswitch import FlexSwitch




########## Port/vlan Ranges#################
fpp_min = 1
fpp_max = 72

svi_min = 1
svi_max = 4094

pc_min = 1
pc_max = 255

loop_min = 1
loop_max = 255

vlan_min = 1
vlan_max = 4094

########## Command auto-completion dictionaries/tree##############


#######################SHOW COMMANDS##########################
_SHOW_BGP_NEIGH={'neighbors':['detail']}
_SHOW_BGP={'bgp':[_SHOW_BGP_NEIGH,'summary']}
_SHOW_OSPF_NEIGH={'neighbors':['detail']}

_SHOW_OSPF={'ospf':[_SHOW_OSPF_NEIGH, 'interface','database']}

_SHOW_ROUTE={'route':['summary','interface','bgp','ospf','static']
			}
_SHOW_PCHANNEL={'summary':['interface'], 
				'load-balance':[''], 
				'interface':['detail']
				}
_INTERFACES=('fpPort','loopback','mgmt','svi','port-channel','cpu')

_SHOW_INTERFACE={_INTERFACES:['counters','detail', 'status']}

_SHOW_IP_INT={'interface':['brief']}

_SHOW_RUN={'run':['bgp','ospf','interface','port-channel']}

_SHOW_ARP={'arp':['summary','detail']}

_SHOW_VLAN={'vlan':['summary','id']}

_SHOW_BFD={'bfd':['neighbors','interfaces']}

#BASE for all show commands	
		

_SHOW_BASE = {'ip':[_SHOW_BGP,_SHOW_ROUTE,_SHOW_OSPF,_SHOW_IP_INT,_SHOW_ARP],
			'version':[''], 'inventory':['detail'], 'interface':[_SHOW_INTERFACE,'counters', 'status'],
			'port-channel':_SHOW_PCHANNEL,'bfd':['interface','summary'],'vlan':[_SHOW_VLAN],'run':[_SHOW_RUN],
			'bfd':[_SHOW_BFD]
			}


#######################CONFIGURE COMMANDS##########################

class Commands():

	def __init__(self,switch_ip):
   		"""init class """
   		self.fs_info = FlexSwitch_info(switch_ip)

   	def parser(self, list, line):
   		match=[]  
   		#Passed get of dictionary for commands, which should be a list. Loop through that list
   		#Items in list could be another dictionary or just a string (could also be a list of strings, but going to try and prevent that)
   		#Dictionary Key in that list could be a tuple (Like interfaces, which could have multiple matches for the same key, hence a tuple).
   		#Check to see if it is a dictionary or list or value.  Check if key is string or tuple of strings.   
   		#loop through strings and compare to user input, checking what the strings start with. 
   		#if multiple matches found print items are ambiguous and return 
   		#else return match with command string from dictionary and use it to proceed down the tree. 
		for key in list:
			if type(key) is types.DictType:
				for command, val in key.items():
					if type(command) is types.TupleType:
						for tup_com in command:
							if tup_com.startswith(line):
								match.append(tup_com)
					elif  command.startswith(line):
						match.append(command)
			elif type(key) is types.ListType:
				for command in key:
					if command.startswith(line):
						match.append(command)
			else: 
				if key.startswith(line):
					match.append(key)
		if len(match):
			if len(match) > 1:
				sys.stdout.write('% Ambiguous Command\n')
				return str(False),match
			else:
				return str(True),match
		else:
			sys.stdout.write('   % Invalid Command\n') 
			return str(False),match

   	def autocomp_parser(self, list, line):
   		match=[]  
   		all=[]
   		#Passed get of dictionary for commands, which should be a list. Loop through that list
   		#Items in list could be another dictionary or just a string (could also be a list of strings, but going to try and prevent that)
   		#Dictionary Key in that list could be a tuple (Like interfaces, which could have multiple matches for the same key, hence a tuple).
   		#Check to see if it is a dictionary or list or value.  Check if key is string or tuple of strings.   
   		#loop through strings and compare to user input, checking what the strings start with. 
   		#if multiple matches found print items are ambiguous and return 
   		#else return match with command string from dictionary and use it to proceed down the tree. 
		for key in list:
			if type(key) is types.DictType:
				for command, val in key.items():
					if type(command) is types.TupleType:
						for tup_com in command:
							if tup_com.startswith(line):
								match.append(tup_com)
					elif  command.startswith(line):
						match.append(command)
			elif type(key) is types.ListType:
				for command in key:
					if command.startswith(line):
						match.append(command)
			else: 
				if key.startswith(line):
					match.append(key)
		if len(match):
			return match
			
	def show_commands(self, arg):
		" Show running system information "
		line=arg.split()
		if len(line)>=1:
			bool, arg1 = self.parser(_SHOW_BASE,line[0] )
			if bool == "True":
				bool=None
				if 'ip' in arg1:
				   if len(line) >= 2:
					   bool, arg2 = self.parser(_SHOW_BASE.get('ip'),line[1])
					   if bool == "True":
						   bool=None
						   if 'bgp' in arg2:
							   if len(line) >=3:
								   bool, arg3 = self.parser(_SHOW_BGP.get('bgp'),line[2])
								   if bool == "True":
									   bool=None
									   if 'neighbors' in arg3:
										  sys.stdout.write("print bgp neighbor\n")
									   elif 'summary' in arg3:
										  self.fs_info.displayBGPPeers()	    				
								   	   else:
								   	  	  sys.stdout.write("% Invalid Command\n")
		  
							   else:
									self.fs_info.displayBGPtable()	
						   elif 'route' in arg2:
							   if len(line) >=3:
								   bool, arg3 = self.parser(_SHOW_ROUTE.get('route'),line[2])
								   if bool == "True":
								      bool=None
								      if 'summary' in arg3:
								      	sys.stdout.write("print route summary\n")
								      elif 'interface' in arg3:
								      	sys.stdout.write("print route interface stuff\n")								      
								      elif 'bgp' in arg3:
								      	sys.stdout.write("print bgp routes\n")								      
								      elif 'ospf' in arg3:
								      	sys.stdout.write("print ospf routes\n")
								      elif 'static' in arg3:
								      	sys.stdout.write("print static routes\n")
								      elif 'connected' in arg3:
								      	sys.stdout.write("print connected routes\n")	
								      else:
								      	sys.stdout.write("% Invalid Command\n")							      								      
							   else:
							       self.fs_info.displayRoutes()
						   elif 'arp' in arg2:
							   if len(line) >=3:
								   bool, arg3 = self.parser(_SHOW_ARP.get('arp'),line[2])
								   if bool == "True":
								      bool=None
								      if 'summary' in arg3:
								      	sys.stdout.write("print arp summary\n")
								      elif 'interface' in arg3:
								      	sys.stdout.write("print arp interface goo\n")
								      else:
								   	  	sys.stdout.write("% Invalid Command\n")
							   else:
									self.fs_info.displayARPEntries()
						   elif 'ospf' in arg2:
							   if len(line) >=3:
								   bool, arg3 = self.parser(_SHOW_OSPF.get('ospf'),line[2])
								   if bool == "True":
								      bool=None
								      if 'interface' in arg3:
								   		self.fs_info.verifyDRElectionResult()
								      elif 'database' in arg3:
								   	    sys.stdout.write("print ospf database\n")
								      elif 'neighbor' in arg3:
								   	  	sys.stdout.write("print ospf neighbors\n")
								      else:
								   	  	sys.stdout.write("% Invalid Command\n")
							   else:
							   		sys.stdout.write("% Incomplete Command\n")
						   elif 'interface' in arg2:
							   if len(line) >=3:
								   bool, arg3 = self.parser(_SHOW_IP_INT.get('interface'),line[2])
								   if bool == "True":
								      bool=None
								      if 'brief' in arg3:
								   		self.fs_info.IPv4Intfstatus()
							   else:
							   		sys.stdout.write("% Incomplete Command\n")

				elif 'interface' in arg1:
				   if len(line) >= 2:
					   bool, arg2 = self.parser(_SHOW_BASE.get('interface'),line[1])
					   if bool == "True":
						   bool=None
						   if 'fpPort' in arg2:
							   if len(line) >=3:
							       if fpp_min <= int(line[2]) <= fpp_max:
									   bool, arg3 = self.parser(_SHOW_INTERFACE.get(_INTERFACES),line[3])
									   if bool == "True":
										   bool=None
										   if 'counters' in arg3:
											  sys.stdout.write("fpPort Counters \n")	
										   elif 'status' in arg3:
											  sys.stdout.write("fpPort status \n")
										   elif 'details' in arg3:
											  sys.stdout.write("fpPort details \n")
							       else:
								       sys.stdout.write("% Invalid interface range \n")
										
						   elif 'svi' in arg2:
							   if len(line) >=3:
							       if svi_min <= int(line[2]) <= svi_max:
									   bool, arg3 = self.parser(_SHOW_INTERFACE.get(_INTERFACES),line[3])
									   if bool == "True":
										   bool=None
										   if 'counters' in arg3:
											  sys.stdout.write("svi Counters \n")	
										   elif 'status' in arg3:
											  sys.stdout.write("svi status \n")
										   elif 'details' in arg3:
											  sys.stdout.write("svi details \n")
							       else:
								       sys.stdout.write("% Invalid svi value \n")											
						   elif 'loopback' in arg2:
							   if len(line) >=3:
							       if loop_min <= int(line[2]) <= loop_max:
									   bool, arg3 = self.parser(_SHOW_INTERFACE.get(_INTERFACES),line[3])
									   if bool == "True":
										   bool=None
										   if 'counters' in arg3:
											  sys.stdout.write("loopback Counters \n")	
										   elif 'status' in arg3:
											  sys.stdout.write("loopback status \n")
										   elif 'details' in arg3:
											  sys.stdout.write("loopback details \n")
							       else:
								       sys.stdout.write("% Invalid loopback value \n")	
						   elif 'port-channel' in arg2:
							   if len(line) >=3:
							       if pc_min <= int(line[2]) <= pc_max:
									   bool, arg3 = self.parser(_SHOW_INTERFACE.get(_INTERFACES),line[3])
									   if bool == "True":
										   bool=None
										   if 'counters' in arg3:
											  sys.stdout.write("port-channel Counters \n")	
										   elif 'status' in arg3:
											  sys.stdout.write("port-channel status \n")
										   elif 'details' in arg3:
											  sys.stdout.write("port-channel details \n")
							       else:
								       sys.stdout.write("% Invalid port-channel value \n")	
						   elif 'eth0' in arg2:
							   if len(line) >=3:
								   bool, arg3 = self.parser(_SHOW_INTERFACE.get(_INTERFACES),line[2])
								   if bool == "True":
									   bool=None
							           if 'counters' in arg3:
							              sys.stdout.write("eth0 Counters \n")	
							           elif 'status' in arg3:
							              sys.stdout.write("eth0 status \n")
							           elif 'details' in arg3:
							              sys.stdout.write("eth0 details \n")
						   elif 'cpu' in arg2:
							   if len(line) >=3:
								   bool, arg3 = self.parser(_SHOW_INTERFACE.get(_INTERFACES),line[2])
								   if bool == "True":
									   bool=None
							           if 'counters' in arg3:
							              self.fs_info.displayCPUPortObjects()	
							           elif 'status' in arg3:
							              sys.stdout.write("CPU status \n")
							           elif 'details' in arg3:
							              sys.stdout.write("CPU details \n")
						   elif 'counters' in arg2:
						       if len(line) >=3:
								   sys.stdout.write("% Invalid command \n")
						       else:
								   self.fs_info.displayPortObjects()				
						   elif 'status' in arg2:
						       self.fs_info.displayPortStatus()
							
				   else: 
				      sys.stdout.write("% Incomplete command \n")	
				      
				      
				elif 'vlan' in arg1:
				   if len(line) >= 2:
					   bool, arg2 = self.parser(_SHOW_VLAN.get('vlan'),line[1])
					   if bool == "True":
						   bool=None
						   if 'summary' in arg2:
						       sys.stdout.write('Print summary vlan Info\n')
						       #self.fs_info.getVlanInfo()
						   elif 'id' in arg2:
						      if len(line) == 3:
						      	if vlan_min <= int(line[2]) <= vlan_max:
						      	 	self.fs_info.displayVlanInfo(line[2])
						      	else:
						      	 	sys.stdout.write("% Invalid Vlan Range \n")
						      else:
						      	 sys.stdout.write("% Incomplete command \n")
				   else:	   	
						self.fs_info.displayVlanInfo()

						#sys.stdout.write('% Incomplete command\n')
				elif 'port-channel' in arg1:
				   if len(line) >= 2:
					   bool, arg2 = self.parser(_SHOW_PCHANNEL,line[1])
					   if bool == "True":
						   bool=None
						   if 'summary' in arg2:
							     self.fs_info.getLagGroups()
						   elif 'interface' in arg2:       				
							   if len(line) >= 3:
							       bool, arg3 = self.parser(_SHOW_PCHANNEL.get('interface'),line[1])
							       print bool
							       if bool == "True":
							          bool=None 
							          if 'detail' in arg3:
							             print  "Running LACP detail"
							             self.fs_info.getLagMembers_detail()
							   else:
								   self.fs_info.getLagMembers()  
					  		  
				   else: 
				      sys.stdout.write("% Incomplete command \n")	
				elif 'run' in arg1:
				   if len(line) >= 2:
					   bool, arg2 = self.parser(_SHOW_RUN.get('run'),line[1])
					   if bool == "True":
						   bool=None
						   if 'bgp' in arg2:
						   	  print "Running BGP JSON"
				elif 'bfd' in arg1:
				   if len(line) >= 2:
					   bool, arg2 = self.parser(_SHOW_BFD.get('bfd'),line[1])
					   if bool == "True":
						   bool=None
						   if 'neighbors' in arg2:
						      self.fs_info.displayBfdNeigh()
						   if 'interfaces' in arg2:
						      self.fs_info.displayBfdInt()				
				

		else:
			sys.stdout.write("% Incomplete Command\n")

	def auto_show(self, text, line, begidx, endidx):
		lines=line.split()
		list=[]	
		
		if len(lines)>=1:
			arg1 = self.autocomp_parser(_SHOW_BASE,lines[1] )
			
			if len(arg1)==1:
				return [i for i in arg1 if i.startswith(text)]
			else:	
				return [i for i in arg1 if i.startswith(text)]
				if 'ip' in arg1:
				   if len(lines)==2:
				   	   return [i for i in arg1 if i.startswith(text)]
				   else:
					   arg2 = self.autocomp_parser(_SHOW_BASE.get('ip'),lines[2])
					   return [i for i in arg2 if i.startswith(text)]
					   if 'bgp' in arg2:
						   if len(lines)<=3:
						   	return [i for i in arg2 if i.startswith(text)]
						   else:
							   arg3 = self.autocomp_parser(_SHOW_BGP.get('bgp'),lines[3])
							   if 'neighbors' in arg3:
							       if len(lines)<=4:
							          return [i for i in arg3 if i.startswith(text)]
							       #else:
							       
							   elif 'summary' in arg3:
								   return
					   else:
						   return [i for i in _SHOW_BASE.get('ip') if i.startswith(text)]	
				else:
					return [i for i in _SHOW_BASE if i.startswith(text)]
		
		
		'''				       
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
			'''

	def global_commands(self, arg):
		""" Global Configuration Commands """
	
	def interface_commands(self, arg):
		"""Interface configuration Commands"""
		
   		
class FlexSwitch_info():

   def __init__(self,switch_ip):
   		self.switch_ip=switch_ip
   		self.swtch = FlexSwitch(self.switch_ip,8080)


   def displayRunBGP(self):
     	routes = self.swtch.getObjects('BGPNeighborStates')
     	if len(routes)>=0:
     	    print '\n'
     	    print 'Network            Mask         NextHop         Cost       Protocol   IfType IfIndex'
     	for rt in routes:
     	    print '%s %s %s %4d   %9s    %5s   %4s' %(rt['DestinationNw'].ljust(15),) 
   		
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
			   print 'Neighbor   LocalAS   PeerAS     State      RxNotifications    RxUpdates   TxNotifications TxUpdates  Description'
		   for pr in peers:
			   print '%s %s %s     %s       %s              %s              %s           %s	%s' %(pr['Object']['NeighborAddress'].ljust(12),
																				  str(pr['Object']['LocalAS']).ljust(8),
																				  pr['Object']['PeerAS'],
																				  sessionState[int(pr['Object']['SessionState'] -1)],
																				  pr['Object']['Messages']['Received']['Notification'],
																				  pr['Object']['Messages']['Received']['Update'],
																				  pr['Object']['Messages']['Sent']['Notification'],
																				  pr['Object']['Messages']['Sent']['Update'],
																				  pr['Object']['Description'])

		   print "\n" 
		   
   def displayBGPtable(self):
     	routes = self.swtch.getObjects('BGPRoutes')
     	if len(routes)>=0:
     	    print '\n'
     	    print 'Network          Mask           NextHop          Metric     LocalPref      Updated   		Path'
     	for rt in routes:
     	    print '%s %s %s %4d   %9d    %14s   %13s' %(rt['Object']['Network'].ljust(17), 
     	                                                    str(rt['Object']['CIDRLen']).ljust(13),
     	                                                    rt['Object']['NextHop'].ljust(15), 
     	                                                    rt['Object']['Metric'], 
     	                                                    rt['Object']['LocalPref'], 
     	                                                    rt['Object']['Updated'].split(".")[0],
     	                                                    rt['Object']['Path'])
        print "\n"

   def displayBfdNeigh(self):
     	neigh = self.swtch.getObjects('BfdSessionStates')
     	if len(neigh)>=0:
     	    print '\n'
     	    print 'Session ID            LocalIP         RemoteIP         LState 	RState  LDiscrim    RDiscrim'
     	for rt in neigh:
     	    print '%s %s %s %4d   %9s    %5d   %4d' %(str(rt['Object']['SessionId']).ljust(15), 
     	                                                    rt['Object']['LocalIpAddr'].ljust(15),
     	                                                    rt['Object']['RemoteIpAddr'].ljust(15), 
     	                                                    rt['Object']['SessionState'], 
     	                                                    rt['Object']['RemoteSessionState'], 
     	                                                    rt['Object']['LocalDiscriminator'], 
     	                                                    rt['Object']['RemoteDiscriminator'])

     	    print 'TxPackets          RxPackets         Multiplier 	MinTxInt  MinRxInt 	 LocalDiag    IfIndex '
     	    print '%s %s %s %4d   %9s    %5s   %4s' %(rt['Object']['NumTxPackets'].ljust(15), 
     	                                                    rt['Object']['NumRxPackets'].ljust(15),
     	                                                    rt['Object']['LocalMultiplier'].ljust(15), 
     	                                                    rt['Object']['DesiredMinTxInterval'], 
     	                                                    rt['Object']['RequiredMinRxInterval'], 
     	                                                    rt['Object']['LocalDiagType'], 
     	                                                    rt['Object']['IfIndex'])
     	    print "********************************************************************************************"
     	print "\n"        

   def displayBfdInt(self):
   		int = self.swtch.getObjects('BfdIntfStates')
   		if len(int)>=0:
   			print '\n'
   			print 'ifIndex   Enabled    NumSessions    Multiplier 	 MinTxInt  MinRxInt'
   		for rt in int:
   			print '%s %s %s %s %s %s' %(str(rt['Object']['IfIndex']).ljust(10), 
     	                                                    str(rt['Object']['Enabled']).ljust(15),
     	                                                    str(rt['Object']['NumSessions']).ljust(10),
     	                                                    str(rt['Object']['LocalMultiplier']).ljust(10), 
     	                                                    rt['Object']['DesiredMinTxInterval'], 
     	                                                    rt['Object']['RequiredMinRxInterval'])                                                    
   		print "\n"   			
	   
   def displayRoutes(self):
     	routes = self.swtch.getObjects('IPv4RouteStates')
     	if len(routes)>=0:
     	    print '\n'
     	    print 'Network         NextHop         Protocol         IfType         IfIndex'
     	for rt in routes:
     	    print '%s %s %s   %s    %s ' %(rt['Object']['DestinationNw'].ljust(15), 
     	                                                    rt['Object']['NextHopIp'].ljust(15), 
     	                                                    rt['Object']['Protocol'].ljust(15), 
     	                                                    rt['Object']['OutgoingIntfType'].ljust(15), 
     	                                                    rt['Object']['OutgoingInterface'].ljust(15))
        print "\n"


   def displayARPEntries(self):
        arps = self.swtch.getObjects('ArpEntrys')
        if len(arps)>=0:
            print '\n'
            print 'IP Address	MacAddress   	    TimeRemaining  	Vlan 	  Intf'
        for d in arps:
            print  '%s	%s    %s	 %s	%s' %(d['Object']['IpAddr'],
						d['Object']['MacAddr'],
						d['Object']['ExpiryTimeLeft'],
						d['Object']['Vlan'],
						d['Object']['Intf'])
        print "\n"

   def IPv4Intfstatus(self):
     	ip_int = self.swtch.getObjects('IPv4Intfs')
     	if len(ip_int)>=0:
     	    print '\n'
     	    print 'Interface     IfIndex        IPv4'
     	for d in ip_int:
     		if len(str(d['Object']['IfIndex'])) < 8:
     			if d['Object']['IfIndex'] < 73:
     				index = self.swtch.getObjects('PortStates')
     				for e in index:
     					if e['Object']['IfIndex'] == d['Object']['IfIndex']:
     						port=e['Object']['Name']
     						break
     					else:
     						port='N/A'
     			else:
     				index = self.swtch.getObjects('Vlans')
     				for e in index:
     					if e['Object']['IfIndex'] == d['Object']['IfIndex']:
     						port=e['Object']['VlanName']
     						break
     					else:
     						port='N/A'
     							
     			print '%s %6s %21s' %(port.ljust(10), 
     						d['Object']['IfIndex'],
     					    d['Object']['IpAddr']
     		               )
     		elif len(str(d['Object']['IfIndex'])) >= 8:
     			if d['Object']['IfIndex'] < 73:
     				index = self.swtch.getObjects('PortStates')
     				for e in index:
     					if e['Object']['IfIndex'] == d['Object']['IfIndex']:
     						port=e['Object']['Name']
     						break
     					else:
     						port='N/A'
     			else:
     				index = self.swtch.getObjects('Vlans')
     				for e in index:
     					if e['Object']['IfIndex'] == d['Object']['IfIndex']:
     						port=e['Object']['VlanName']
     						break
     					else:
     						port='N/A'
     							
     			print '%s %s %13s' %(port.ljust(10), 
     						d['Object']['IfIndex'],
     					    d['Object']['IpAddr']
     		               )     			
     		     	       
        print "\n"  
        
   def displayPortObjects(self):
        ports = self.swtch.getObjects('PortStates')
        if len(ports):
            print '\n'
            print 'Port         InOctets   InUcastPkts   InDiscards  InErrors     InUnknownProtos   OutOctets OutUcastPkts   OutDiscards   OutErrors'
        for d in ports:
            if d['Object']['IfIndex'] == 0:
        		continue
            elif d['Object']['IfIndex'] < 10:
            	print '%s  %8d %10d   %10d    %8d   %15d   %9d   %12d   %11d   %11d' %("fpPort-"+str(d['Object']['IfIndex']),
                                                                d['Object']['IfInOctets'],
                                                                d['Object']['IfInUcastPkts'],
                                                                d['Object']['IfInDiscards'],
                                                                d['Object']['IfInErrors'],
                                                                d['Object']['IfInUnknownProtos'],
                                                                d['Object']['IfOutOctets'],
                                                                d['Object']['IfOutUcastPkts'],
                                                                d['Object']['IfOutDiscards'],
                                                                d['Object']['IfOutErrors'])
            else:
            	print '%s  %7d %10d   %10d    %8d   %15d   %9d   %12d   %11d   %11d' %("fpPort-"+str(d['Object']['IfIndex']),
                                                                d['Object']['IfInOctets'],
                                                                d['Object']['IfInUcastPkts'],
                                                                d['Object']['IfInDiscards'],
                                                                d['Object']['IfInErrors'],
                                                                d['Object']['IfInUnknownProtos'],
                                                                d['Object']['IfOutOctets'],
                                                                d['Object']['IfOutUcastPkts'],
                                                                d['Object']['IfOutDiscards'],
                                                                d['Object']['IfOutErrors'])
        print "\n"
   def displayCPUPortObjects(self):
        ports = self.swtch.getObjects('PortStates')
        if len(ports):
            print '\n'
            print 'Port         InOctets   InUcastPkts   InDiscards  InErrors     InUnknownProtos   OutOctets OutUcastPkts   OutDiscards   OutErrors'
        for d in ports:
            if d['Object']['IfIndex'] == 0:
            	print '%s  %8d %10d   %10d    %8d   %15d   %9d   %12d   %11d   %11d' %("CPU",
                                                                d['Object']['IfInOctets'],
                                                                d['Object']['IfInUcastPkts'],
                                                                d['Object']['IfInDiscards'],
                                                                d['Object']['IfInErrors'],
                                                                d['Object']['IfInUnknownProtos'],
                                                                d['Object']['IfOutOctets'],
                                                                d['Object']['IfOutUcastPkts'],
                                                                d['Object']['IfOutDiscards'],
                                                                d['Object']['IfOutErrors'])

   def displayPortStatus(self):
        ports = self.swtch.getObjects('PortStates')
        if len(ports):
            print '\n'
            print 'Port         Status   IFIndex   Duplex   Speed     Type'
        for d in ports: 
            if d['Object']['IfIndex'] == 0:
        		continue
            elif d['Object']['IfIndex'] < 10:
            	print '%s  %8s %6s %10s %8s %9s' %("fpPort-"+str(d['Object']['IfIndex']),
                                                            d['Object']['OperState'],
                                                             d['Object']['IfIndex'],
                                                             'N/A',
                                                             'N/A',
                                                             'N/A')
            else:
            	print '%s  %7s %6s %10s %8s %9s' %("fpPort-"+str(d['Object']['IfIndex']),
                                                            d['Object']['OperState'],
                                                             d['Object']['IfIndex'],
                                                             'N/A',
                                                             'N/A',
                                                             'N/A')
   def displayVlanInfo(self, vlanId=0):
   		if vlanId == 0:
   			vlans = self.swtch.getObjects('Vlans')
   			if len(vlans):
   				print 'Vlan    Status   Ports 	Untagged_Ports'
   			for d in vlans:
   				print '%s  %8s %8s %8s' %(str(d['Object']['VlanId']),
   									  d['Object']['OperState'],
   									  d['Object']['IfIndexList'],
   									  d['Object']['UntagIfIndexList'])   			
   		else:
   			vlans = self.swtch.getObjects('Vlans')
   			if len(vlans):
   				print 'Vlan    Status   Ports 	Untagged_Ports'   		
   		   	for d in vlans:
   				if d['Object']['VlanId'] == int(vlanId):
   					print '%s  %8s %8s %8s' %(str(d['Object']['VlanId']),
   									  	d['Object']['OperState'],
   									  	d['Object']['IfIndexList'],
   									  	d['Object']['UntagIfIndexList'])   
   									  	

   def verifyDRElectionResult(self):
        ospfIntfs = self.swtch.getObjects('OspfIfEntryStates')
        print '\n'
        #self.assertNotEqual(len(ospfIntfs) != 0)
        if len(ospfIntfs)>=0:
            print 'IfAddr IfIndex  State  DR-RouterId DR-IpAddr BDR-RouterI BDR-IpAddr NumEvents LSACount LSACksum'

        for d in ospfIntfs:
            #if sum(d['ospfIntfs']):
                print '%3s  %3d %10s   %10s    %8s   %15s   %9s   %12s   %11s   %11s' %( d['Object']['IfIpAddressKey'],
                                                                                        d['Object']['AddressLessIfKey'],
                                                                                        d['Object']['IfState'],
                                                                                        d['Object']['IfDesignatedRouter'],
                                                                                        d['Object']['IfBackupDesignatedRouter'],
                                                                                        d['Object']['IfEvents'],
                                                                                        d['Object']['IfLsaCount'],
                                                                                        d['Object']['IfLsaCksumSum'],
                                                                                        d['Object']['IfDesignatedRouterId'],
                                                                                        d['Object']['IfBackupDesignatedRouterId'])
        print "\n"            

   def getLagMembers(self):
      members = self.swtch.getObjects('AggregationLacpMemberStateCounterss')
      print '\n---- LACP Members----'
      if len(members):
   	   for d in members:
   		   print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n'
   		   print 'name: ' + d['Object']['NameKey'] + ' interface: ' + d['Object']['Interface']
   		   print 'enabled: %s' % d['Object']['Enabled']
   		   print 'lagtype: ' + ('LACP' if not d['LagType'] else 'STATIC')
   		   print 'operkey: %s' % d['Object']['OperKey']
   		   print 'mode: ' + ('ACTIVE' if not d['Object']['LacpMode'] else 'PASSIVE')
   		   print 'interval: %s' % (('SLOW' if d['Object']['Interval'] else 'FAST'))
   		   print 'system:\n'
   		   print '\tsystemmac: %s' % d['Object']['SystemIdMac']
   		   print '\tsysteprio: %s' % d['Object']['SystemPriority']
   		   print '\tsystemId: %s' % d['Object']['SystemId']
   		   print 'actor:'
   		   stateStr = '\tstate: '
   		   for s in ('Activity', 'Timeout', 'Aggregatable', 'Synchronization', 'Collecting', 'Distributing'):
   			   if s == 'Synchronization' and not d['Object'][s]:
   				   stateStr += s + ', '
   			   elif s == 'Activity' and not d['Object'][s]:
   				   stateStr += s + ', '
   			   elif s in ('Activity', 'Synchronization'):
   				   continue
   			   elif d[s]:
   				   stateStr += s + ', '
   		   print stateStr.rstrip(',')
   
   		   print '\tstats:'
   		   for s in ('LacpInPkts', 'LacpOutPkts', 'LacpRxErrors', 'LacpTxErrors', 'LacpUnknownErrors', 'LacpErrors', 'LampInPdu', 'LampOutPdu', 'LampInResponsePdu', 'LampOutResponsePdu'):
   			   print '\t' + s, ': ', d['Object'][s]
   
   		   print 'partner:\n'
   		   print '\t' + 'key: %s' % d['Object']['PartnerKey']
   		   print '\t' + 'partnerid: ' + d['Object']['PartnerId']
   


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
   		   print 'name: ' + d['Object']['NameKey'] + ' interface: ' + d['Interface']
   		   print 'enabled: %s' % d['Object']['Enabled']
   		   print 'lagtype: ' + ('LACP' if not d['Object']['LagType'] else 'STATIC')
   		   print 'operkey: %s' % d['Object']['OperKey']
   		   print 'mode: ' + ('ACTIVE' if not d['Object']['LacpMode'] else 'PASSIVE')
   		   print 'interval: %s' % (('SLOW' if d['Object']['Interval'] else 'FAST'))
   		   print 'system:\n'
   		   print '\tsystemmac: %s' % d['Object']['SystemIdMac']
   		   print '\tsysteprio: %s' % d['Object']['SystemPriority']
   		   print '\tsystemId: %s' % d['Object']['SystemId']
   		   print 'actor:'
   		   stateStr = '\tstate: '
   		   for s in ('Activity', 'Timeout', 'Aggregatable', 'Synchronization', 'Collecting', 'Distributing'):
   			   if s == 'Synchronization' and not d['Object'][s]:
   				   stateStr += s + ', '
   			   elif s == 'Activity' and not d['Object'][s]:
   				   stateStr += s + ', '
   			   elif s in ('Activity', 'Synchronization'):
   				   continue
   			   elif d[s]:
   				   stateStr += s + ', '
   		   print stateStr.rstrip(',')
   
   		   print '\tstats:'
   		   for s in ('LacpInPkts', 'LacpOutPkts', 'LacpRxErrors', 'LacpTxErrors', 'LacpUnknownErrors', 'LacpErrors', 'LampInPdu', 'LampOutPdu', 'LampInResponsePdu', 'LampOutResponsePdu'):
   			   print '\t' + s, ': ', d['Object'][s]
   
   		   print 'partner:\n'
   		   print '\t' + 'key: %s' % d['Object']['PartnerKey']
   		   print '\t' + 'partnerid: ' + d['Object']['PartnerId']
   		   print 'debug:\n'
   		   try:
   			   print '\t' + 'debugId: %s' % d['Object']['DebugId']
   			   print '\t' + 'RxMachineState: %s' % RxMachineStateDict[d['Object']['RxMachine']]
   			   print '\t' + 'RxTime (rx pkt rcv): %s' % d['Object']['RxTime']
   			   print '\t' + 'MuxMachineState: %s' % MuxMachineStateDict[d['Object']['MuxMachine']]
   			   print '\t' + 'MuxReason: %s' % d['Object']['MuxReason']
   			   print '\t' + 'Actor Churn State: %s' % ChurnMachineStateDict[d['Object']['ActorChurnMachine']]
   			   print '\t' + 'Partner Churn State: %s' % ChurnMachineStateDict[d['Object']['PartnerChurnMachine']]
   			   print '\t' + 'Actor Churn Count: %s' % d['Object']['ActorChurnCount']
   			   print '\t' + 'Partner Churn Count: %s' % d['Object']['PartnerChurnCount']
   			   print '\t' + 'Actor Sync Transition Count: %s' % d['Object']['ActorSyncTransitionCount']
   			   print '\t' + 'Partner Sync Transition Count: %s' % d['Object']['PartnerSyncTransitionCount']
   			   print '\t' + 'Actor LAG ID change Count: %s' % d['Object']['ActorChangeCount']
   			   print '\t' + 'Partner LAG ID change Count: %s' % d['Object']['PartnerChangeCount']
   		   except Exception as e:
   			   print e      
   
   def getLagGroups(self):
      lagGroup = self.swtch.getObjects('AggregationLacpStates')
      print '\n'
      if len(lagGroup)>=0:
   	   print 'Name      Ifindex      LagType   Description      Enabled   MinLinks   Interval   Mode          SystemIdMac            SystemPriority    HASH'
   
   	   for d in lagGroup:
   		   print '%7s  %7s    %7s  %15s    %8s   %2s     %8s      %6s   %20s         %s              %s' %(d['Object']['NameKey'],
   														   d['Object']['Ifindex'],
   														   "LACP" if int(d['Object']['LagType']) == 0 else "STATIC",
   														   d['Description'],
   														   "Enabled" if bool(d['Object']['Enabled']) else "Disabled",
   														   d['Object']['MinLinks'],
   														   "FAST" if int(d['Object']['Interval']) == 0 else "SLOW",
   														   "ACTIVE" if int(d['Object']['LacpMode']) == 0 else "PASSIVE",
   														   d['Object']['SystemIdMac'],
   														   d['Object']['SystemPriority'],
   														   d['Object']['LagHash'])
