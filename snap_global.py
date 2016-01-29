from cmd import Cmd
import readline
import rlcompleter
import sys
from snap_interface import Interface_CmdLine
from snap_router_ospf import Router_ospf_CmdLine
from snap_router_bgp import Router_bgp_CmdLine
from snap_commands import Commands
from snap_help_commands import Command_help

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
    def __init__(self,CmdLine,switch_ip):
        Cmd.__init__(self)
        if not USING_READLINE:
            self.completekey = None
        self.prompt = "(config)#"
        self.enable = CmdLine
        self.commands = Commands(switch_ip)
        self.intconf = Interface_CmdLine(self,self.enable,switch_ip)
        self.routerospf = Router_ospf_CmdLine(self.enable,switch_ip, self.intconf)
        self.routerbgp = Router_bgp_CmdLine(self.enable,switch_ip, self.intconf)

    def cmdloop(self):
        try:
        	Cmd.cmdloop(self)
        except KeyboardInterrupt as e:
        	self.intro = '\n'
        	self.cmdloop() 
    def default(self, line):
        cmd, arg, line = self.parseline(line)
        cmds = self.completenames(cmd)
        num_cmds = len(cmds)
        if num_cmds == 1:
            getattr(self, 'do_'+cmds[0])(arg)
        elif num_cmds > 1:
            sys.stdout.write('%% Ambiguous command:\t"%s"\n' % cmd)
        else:
            sys.stdout.write('%% Unrecognized command\n')
 
    def emptyline(self):
        pass
        
    def do_exit(self, line):
		" exit Interface Configuration mode and return to Global Configuration mode"
		return True

    def do_end(self, line):
		" Return to enable mode"
		return True
    	   
    def do_interface(self, arg):
    	" Interface configuration mode "
    	args = arg.split()
    	if 'fpPort-' not in args[0]:
    		sys.stdout.write('% Invalid interface\n')
    	else:
    		self.intconf.prompt = self.prompt[:-2] + "-if)#"
    		self.intconf.cmdloop()
    	if "end" in self.intconf.lastcmd:
    		return True
    def do_router(self, arg):
    	" Router configuration mode "
    	args=arg.split()
    	try:
    		if 'bgp' in args[0]:
    			self.routerbgp.prompt = self.prompt[:-2] + "-router)#"
    			self.routerbgp.cmdloop()
    		
    		elif 'ospf' in args[0]:
    			self.routerospf.prompt = self.prompt[:-2] + "-router)#"
    			self.routerospf.cmdloop()
    	except IndexError:
    		sys.stdout.write('% Incomplete command\n')
    	
    	print 	self.routerbgp.lastcmd, self.routerospf.lastcmd
    		  		    	
    	if "end" in self.routerbgp.lastcmd or self.routerbgp.lastcmd:
    		return True
    		
    def do_show(self, line):
        " Show running system information "
        self.commands.show_commands(line)
        #self.enable.do_show(line)
    def complete_show(self, text, line, begidx, endidx):
    	return self.enable.complete_show(text, line, begidx, endidx)
    	
    def precmd(self, line):
        if line.strip() == 'help':
            sys.stdout.write('%s\n' % self.__doc__)
            return ''
        elif line.endswith('?'):
	        return self.command_help.show_help(line)
        return line 
