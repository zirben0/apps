import sys

################ HELP COMMAND TEXT FROM '?' ########################

#######################SHOW COMMANDS##########################

_IP_HELP = {'interface':'Display IP related interface information',
			'route':'Display routing information',
			'arp  ':'Display ARP table and statistics',
			'bgp   ':'Display BGP status and configuration'
					}
_SHOW_HELP = {'version':'Show the software version',
			'interface':'Display IP related interface information',
			'inventory':'Show physical inventory',
			'ip        ':'Display IP information'
					}
_BGP_HELP = {'summary':'Display summarized information of BGP state',
			'neighbors':'Display all configured BGP neighbors',
					}	
_BGP_NEIGH_HELP = {'detail':'Display detailed information for BGP neighbors'
					}
_INVENT_HELP = {'detail':'Display detailed information for device inventory '
					}
_INTERFACE_HELP= {'fpPort':'Front Panel Ports',
  				'loopback':'Loopback interface',
  				'eth0':'Management interface',
  				'port-channel':'Port Channel interface',
  				'svi':'Vlan interface'
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
							
_COMMAND_HELP = {'ip':_IP_HELP,
				'show':_SHOW_HELP, 
				'bgp':_BGP_HELP,
				'route':_ROUTE_HELP,
				'bgp_neigh':_BGP_NEIGH_HELP,
				'inventory':_INVENT_HELP,
				'interface':_INTERFACE_HELP,
				'route_proto':_ROUTE_PROTO_HELP,
				'route_sum':_ROUTE_SUM_HELP
				}

class Command_help():

	def __init__(self):
   		"""init class """
   		#self.fs_info = FlexSwitch_info(switch_ip)
   		
   	def parser(self, dict, line):
		for key in dict.items():
		if  key[0].startswith(line):
			match.append(key)
		print match
		if len(match):
			if len(match) > 1:
				sys.stdout.write('   % Ambiguous Command\n') 
				for i in match:
					sys.stdout.write('   %s\t%s\n' %  i[0],i[1]
				return False
			else:
				return True
					
					
	def show_help(self, lines):
		remove = lines.replace('?','')
		line = remove.split()
		val=''
		#print line[-1], len(line), line[0]
		if parser(dict, line[0])
		if 'show' in line[0] and len(line) >= 1:
		   if len(line) >= 2:
		       if 'ip' in line[1]:
		       	   if len(line) >= 3:
				       if 'bgp' in line[2]:
				       	   if len(line) >=4:
							   if 'neighbors' in line[3]:
								  sys.stdout.write('   <CR>\n')
								  for keys in _COMMAND_HELP.get('bgp_neigh'):
								   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('bgp_neigh').get(keys)) ) 
						  
							   elif 'summary' in line[3]:
								  sys.stdout.write('   <CR>\n')	    				
								
							   elif not [val for key, val in _COMMAND_HELP.get('bgp').items() if line[-1] in key]:
								  sys.stdout.write('% Invalid Command\n')	
												  
				       	   else:
				   				for keys in _COMMAND_HELP.get('bgp'):
				   				    sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('bgp').get(keys)) )										    					
				          
				       elif 'route' in line[2]:
				       	   if len(line) >=4:
							   if 'summary' in line[3]:
								   sys.stdout.write('   <CR>\n')
								   for keys in _COMMAND_HELP.get('route_sum'):
								       sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route_sum').get(keys)) )
							   elif 'interface' in line[3]:
								   sys.stdout.write('   <CR>\n')
								   for keys in _COMMAND_HELP.get('interface'):
								       sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('interface').get(keys)) )
							   elif 'bgp' in line[3]:
								   sys.stdout.write('   <CR>\n')
								   for keys in _COMMAND_HELP.get('route_proto'):
								       sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route_proto').get(keys)) ) 
							   elif 'ospf' in line[3]:
								   sys.stdout.write('   <CR>\n')
								   for keys in _COMMAND_HELP.get('route_proto'):
								       sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route_proto').get(keys)) ) 
							   elif 'static' in line[3]:
								   sys.stdout.write('   <CR>\n')
								   for keys in _COMMAND_HELP.get('route_proto'):
								       sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route_proto').get(keys)) ) 
							   elif 'connected' in line[3]:
								   sys.stdout.write('   <CR>\n')
								   for keys in _COMMAND_HELP.get('route_proto'):
								       sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route_proto').get(keys)) ) 
				       	   else:
				               for keys in _COMMAND_HELP.get('route'):
				       	   		   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('route').get(keys)) ) 	    					
				       
				       elif not [val for key, val in _COMMAND_HELP.get('ip').items() if line[-1] in key]:
				              sys.stdout.write('% Invalid Command\n')
				        
		       	   else:
				   		for keys in _COMMAND_HELP.get('ip'):
				   		    sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('ip').get(keys)) )	
				             
		       elif 'interface' in line[1]:
		           '''goo'''
		           #if len(line) >= 3:
		           	
		           #if 'fpport' in line 	
			       #sys.stdout.write('   <CR>\n')
			       
			   
		       elif 'inventor' in line[1]:
			       sys.stdout.write('   <CR>\n')
			       for keys in _COMMAND_HELP.get('inventory'):
				       sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('inventory').get(keys)) )
			   
		       elif not [val for key in _SHOW_HELP.iteritems() if line[-1] in key[0]]:
			   	   print key, line[-1]
			   	   sys.stdout.write('% Unknown Command\n')  
		       print line[-1]
		   else:
		       for keys in _COMMAND_HELP.get('show'):
				   sys.stdout.write('   %s\t%s\n' % (keys,_COMMAND_HELP.get('show').get(keys)) )
		 				   
		 

		
			
			
			
			       