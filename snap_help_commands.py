import sys

################ HELP COMMAND TEXT FROM '?' ########################

#######################SHOW COMMANDS##########################

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

class Command_help():

	def __init__(self):
   		"""init class """
   		#self.fs_info = FlexSwitch_info(switch_ip)
	def show_help(self, line):
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
