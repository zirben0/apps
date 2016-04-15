import sys

################ HELP COMMAND TEXT FROM '?' ########################

#######################SHOW COMMANDS##########################

_IP_HELP = {'interface':'Display IP related interface information',
			'route':'Display routing information',
			'arp  ':'Display ARP table and statistics',
			'bgp   ':'Display BGP status and configuration',
			'ospf':'Display OSPF status and configurtion',

					}
_SHOW_HELP = {'bfd	       ':'Show Bfd information',
			  'interface   ':'Display IP related interface information',
			  'inventory   ':'Show physical inventory',
			  'ip          ':'Display IP information',
			  'port-channel':'Show port-channel information',
			  'version     ':'Show the software version',

					}
_BGP_HELP = {'summary':'Display summarized information of BGP state',
			'neighbors':'Display all configured BGP neighbors',
					}	
_BGP_NEIGH_HELP = {'detail':'Display detailed information for BGP neighbors'
					}
_BFD_HELP = {'interface':'Display BFD interfaces config',
			'neighbors':'Display all configured BFD neighbors',
					}
_INVENT_HELP = {'detail':'Display detailed information for device inventory '
					}
_INTERFACE_HELP= {'<CR>':'',
				'fpPort':'Front Panel Ports',
  				'loopback':'Loopback interface',
  				'eth0':'Management interface',
  				'port-channel':'Port Channel interface',
  				'svi':'Vlan interface'
  				}

_PORTCHANNEL_HELP= {'summary':'Port-channel summary status',
  					'interface':'Port-channel interface',
  					}
_ARP_HELP = {'<CR>':'',
			'summary':'Display summarized information of arp',
			'detail':'Display detailed formation for arp entries'
			} 
_ROUTE_HELP = 	{'summary':'Display summarized information of routes',
				'interface':'Display routes with next-hop through this interface only',
				'bgp  ':'Display bgp routes ',
				'ospf ':'Display ospf routers',
				'static':'Display static routes',
				'connected':'Display connected routes'
					}	
_ROUTE_PROTO_HELP = {'interface':'Display routes with next-hop through this interface only',
					'summary':'Display route counts',
					'vrf':'Display per-VRF information'
					}
_ROUTE_SUM_HELP = {'vrf':'Display per-VRF information'}

_OSPF_HELP ={'interface':'Display information for OSPF interfaces',
			'neighbors':'Display all configured OSPF neighbors',
			'database':'Display information about OSPF database table'
					}	
							
_COMMAND_HELP = {'show':_SHOW_HELP, 
				'bgp':_BGP_HELP,
				'route':_ROUTE_HELP,
				'bgp_neigh':_BGP_NEIGH_HELP,
				'route_proto':_ROUTE_PROTO_HELP,
				'route_sum':_ROUTE_SUM_HELP,
				'ip':_IP_HELP,
				'inventory':_INVENT_HELP,
				'interface':_INTERFACE_HELP,
				'arp':_ARP_HELP,
				'ospf':_OSPF_HELP,
				'bfd':_BFD_HELP,
				'port-channel':_PORTCHANNEL_HELP
				}


class Command_help():

	def __init__(self):
   		"""init class """
   		#self.fs_info = FlexSwitch_info(switch_ip)
   		
   	def parser(self, dict, line):
   		match=[]
   		info={}
		for key, val in dict.items():
			if  key.startswith(line):
				info = {key:val}
				match.append(info)
		if len(match):
			if len(match) > 1:
				sys.stdout.write('% Ambiguous Command...Choose from the following:\n\n') 
				for i in match:
					for command, descrip in i.items():
						#print command, descrip
						sys.stdout.write('   %s\t%s\n' % ( command,descrip) )
				return str(False),match
			else:
				for i in match:
					for key, val in i.items():
						command=key
				return str(True),command
		else:
			sys.stdout.write('   % Unknown Command\n') 
			return str(False),match
					
					
	def show_help(self, lines):
		remove = lines.replace('?','')
		line = remove.split()
		#print line[-1], len(line), line[0]
		if len(line)>=2:
			bool, arg1 = self.parser(_COMMAND_HELP.get('show'),line[1] )
			if bool == "True":
				bool=None
				if 'ip' in arg1:
				   if len(line) >= 3:
					   bool, arg2 = self.parser(_COMMAND_HELP.get('ip'),line[2])
					   if bool == "True":
						   bool=None
						   if 'bgp' in arg2:
							   if len(line) >=4:
								   bool, arg3 = self.parser(_COMMAND_HELP.get('bgp'),line[3])
								   if bool == "True":
									   bool=None
									   if 'neighbors' in arg3:
										 sys.stdout.write('   <CR>\n')
										 for keys in _COMMAND_HELP.get('bgp_neigh'):
											sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('bgp_neigh').get(keys)) ) 
		   
									   elif 'summary' in arg3:
										  sys.stdout.write('   <CR>\n')	    				
								   #No non ambiguous BGP context match found
								   else:
									   return	
		  
							   else:
									for keys in _COMMAND_HELP.get('bgp'):
										sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('bgp').get(keys)) )										    					

						   elif 'route' in arg2:
							   if len(line) >=4:
								   bool, arg3 = self.parser(_COMMAND_HELP.get('route'),line[3])
								   if bool == "True":
									   bool=None
									   if 'summary' in arg3:
										  sys.stdout.write('   <CR>\n')
										  for keys in _COMMAND_HELP.get('route_sum'):
										   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route_sum').get(keys)) )
									   elif 'interface' in arg3:
										  sys.stdout.write('   <CR>\n')
										  for keys in _COMMAND_HELP.get('interface'):
										   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('interface').get(keys)) )
									   elif 'bgp' in arg3:
										  sys.stdout.write('   <CR>\n')
										  for keys in _COMMAND_HELP.get('route_proto'):
										   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route_proto').get(keys)) ) 
									   elif 'ospf' in arg3:
										  sys.stdout.write('   <CR>\n')
										  for keys in _COMMAND_HELP.get('route_proto'):
										   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route_proto').get(keys)) ) 
									   elif 'static' in arg3:
										  sys.stdout.write('   <CR>\n')
										  for keys in _COMMAND_HELP.get('route_proto'):
										   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route_proto').get(keys)) ) 
									   elif 'connected' in arg3:
										  sys.stdout.write('   <CR>\n')
										  for keys in _COMMAND_HELP.get('route_proto'):
										   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route_proto').get(keys)) )
									#No non ambiguous Route context match found. 
								   else:
									  return 
							   else:
								   for keys in _COMMAND_HELP.get('route'):
									   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route').get(keys)) ) 	   
						   elif 'arp' in arg2:
							   if len(line) >=4:
								   bool, arg3 = self.parser(_COMMAND_HELP.get('arp'),line[3])
								   if bool == "True":
									   bool=None
									   if 'summary' in arg3:
										  sys.stdout.write('   <CR>\n')
									   elif 'detail' in arg3:
									      sys.stdout.write('   <CR>\n')
							   else:
								   for keys in _COMMAND_HELP.get('arp'):
									   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('arp').get(keys)) ) 	   
						   elif 'ospf' in arg2:
							   if len(line) >=4:
								   bool, arg3 = self.parser(_COMMAND_HELP.get('ospf'),line[3])
								   if bool == "True":
									   bool=None
									   if 'neighbor' in arg3:
										  sys.stdout.write('   <CR>\n')
									   elif 'interface' in arg3:
									      sys.stdout.write('   <CR>\n')
									   elif 'database' in arg3:
									      sys.stdout.write('   <CR>\n')
							   else:
								   for keys in _COMMAND_HELP.get('ospf'):
									   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('ospf').get(keys)) ) 	   
		       		       
					# No arg match for ip context
					   else:
						  return
				   else:
						for keys in _COMMAND_HELP.get('ip'):
							sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('ip').get(keys)) )	

				elif 'interface' in arg1:
				   for keys in _COMMAND_HELP.get('interface'):
					   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('interface').get(keys)) )

				elif 'inventory' in arg1:
				   for keys in _COMMAND_HELP.get('inventory'):
					   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('inventory').get(keys)) )
				elif 'version' in arg1:
				   sys.stdout.write('   <CR>\n')
				   
				elif 'bfd' in arg1:
				   if len(line) >= 3:
					   bool, arg2 = self.parser(_COMMAND_HELP.get('bfd'),line[2])
					   if bool == "True":
						   bool=None
						   if 'neighbor' in arg2:	
								sys.stdout.write('   <CR>\n')							   
						   elif 'interface' in arg2:	
								sys.stdout.write('   <CR>\n')
				   else:
					   for keys in _COMMAND_HELP.get('bfd'):
						   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('bfd').get(keys)) ) 

				elif 'port-channel' in arg1:
				   if len(line) >= 3:
					   bool, arg2 = self.parser(_COMMAND_HELP.get('port-channel'),line[2])
					   if bool == "True":
						   bool=None
						   if 'summary' in arg2:	
								sys.stdout.write('   <CR>\n')							   
						   elif 'interface' in arg2:	
								sys.stdout.write('   <CR>\n')
		#No args presented after "show"; I.E. show ?
		else: 
			for keys in _COMMAND_HELP.get('show'):
				sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('show').get(keys)) )			   
		 

		
			
			
			
			       