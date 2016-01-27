#!/usr/bin/python

import sys
import socket
from cmd import Cmd
import cmd
import readline
import rlcompleter

_SHOW_BGP_NEIGH={'neighbors':['detail']}
_SHOW_BGP={'bgp':[_SHOW_BGP_NEIGH,'summary']}
_SHOW_ROUTE={'route':['summary', 'interface', 'bgp', 'ospf', 'static']}
_SHOW_BASE = {'ip':[_SHOW_BGP,_SHOW_ROUTE,'interface'],'version':[''], 'inventory':['detail'], 'interface':['']}

_IP_HELP = {'summary':'Display summarized information of BGP state',
			'interface':'Display IP related interface information',
			'route':'Display routing information'
					}
_SHOW_HELP = {'version':'Show the software version',
			'interface':'Display IP related interface information',
			'inventory':'Show physical inventory'
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
        #BGP
        if "?" in self.lastcmd:
        	return 
        if 'ip' in arg:
        	if 'bgp' in arg:
        		#print bgp table
        		if 'neighbors' in arg:
        			#print BGP neighbors
        			sys.stdout.write("neighbor\n")
        		elif 'summary' in arg:
        			sys.stdout.write("summary\n")
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
 
class Global_CmdLine(Cmd):  
    """
    Global Configuration Mode.  Place where Global configuration for the device 
    can be applied. 
    
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
        self.prompt = "(config)#"
    def default(self, line):
        cmd, arg, line = self.parseline(line)
        cmds = self.completenames(cmd)
        num_cmds = len(cmds)
        if num_cmds == 1:
            getattr(self, 'do_'+cmds[0])(arg)
        elif num_cmds > 1:
            sys.stdout.write('%% Ambiguous command:\t"%s"\n' % cmd)
        else:
            sys.stdout.write('% Unrecognized command\n')
 
    def emptyline(self):
        pass
        
    def do_exit(self, line):
		" exit Interface Configuration mode and return to Global Configuration mode"
		return True

    def do_end(self, line):
		" Return to enable mode"
		return True
    	   
    def do_interface(self, args):
		" Global configuration mode "
		intconf = Interface_CmdLine()
		intconf.prompt = self.prompt[:-2] + "-if)#"
		intconf.cmdloop()
		if "end" in intconf.lastcmd:
			return True

    def precmd(self, line):
        if line.strip() == 'help':
            sys.stdout.write('%s\n' % self.__doc__)
            return ''
        cmd, arg, line = self.parseline(line)
        if arg == '?':
            cmds = self.completenames(cmd)
            if cmds:
                self.columnize(cmds)
                sys.stdout.write('\n')
            return ''
        return line           
class Interface_CmdLine(Cmd):  
    """
     Interace Configuration Mode.  Place where interface configuration for the device 
     can be applied. 
     
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
        self.prompt = "(config-if)#"
    def default(self, line):
        cmd, arg, line = self.parseline(line)
        cmds = self.completenames(cmd)
        num_cmds = len(cmds)
        if num_cmds == 1:
            getattr(self, 'do_'+cmds[0])(arg)
        elif num_cmds > 1:
            sys.stdout.write('%% Ambiguous command:\t"%s"\n' % cmd)
        else:
            sys.stdout.write('% Unrecognized command\n')
    
    def emptyline(self):
        pass    
    def do_exit(self, line):
    	" exit Interface Configuration mode and return to Global Configuration mode"
    	return True
    def do_end(self, line):
    	" Return to enable mode"
    	return True
    def precmd(self, line):
        if line.strip() == 'help':
            sys.stdout.write('%s\n' % self.__doc__)
            return ''
        cmd, arg, line = self.parseline(line)
        if arg == '?':
            cmds = self.completenames(cmd)
            if cmds:
                self.columnize(cmds)
                sys.stdout.write('\n')
            return ''
        return line           
    	
# *** MAIN LOOP ***
if __name__ == '__main__':
    cmdLine = CmdLine()
    cmdLine.cmdloop()
