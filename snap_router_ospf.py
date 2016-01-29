from cmd import Cmd
import readline
import rlcompleter
import sys
#from snap_interface import Interface_CmdLine


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
        
class Router_ospf_CmdLine(Cmd):  
    """
    Router Configuration Mode.  Place where Router configuration for the device 
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
    def __init__(self,CmdLine,FlexSwitch_info,Interface_CmdLine):
        Cmd.__init__(self)
        if not USING_READLINE:
            self.completekey = None
        self.prompt = "(config-router)#"
        self.enable = CmdLine
        self.interface = Interface_CmdLine
        self.fs_info = FlexSwitch_info

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
		self.interface.do_interface(line)
    		
    def do_show(self, line):
        " Show running system information "
        self.enable.do_show(line)
    def complete_show(self, text, line, begidx, endidx):
    	return self.enable.complete_show(text, line, begidx, endidx)
    	
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
