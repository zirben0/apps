#!/usr/bin/python

import sys
from cmd import Cmd
import readline
import rlcompleter
if 'libedit' in readline.__doc__:
    readline.parse_and_bind("bind ^I rl_complete")
else:
    readline.parse_and_bind("tab: complete")
    
USING_READLINE = True
try:
    # For platforms without readline support go visit ...
    # http://pypi.python.org/pypi/readline/
    import readline
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
        self.prompt = "#"
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
    
    def do_help(self, arg):
        doc_strings = [ (i[3:], getattr(self, i).__doc__)
            for i in dir(self) if i.startswith('do_') ]
        doc_strings = [ '  %s\t%s\n' % (i, j)
            for i, j in doc_strings if j is not None ]
        sys.stdout.write('Commands:\n%s\n' % ''.join(doc_strings))
 
    def do_configure(self, args):
		" Global configuration mode "
		gconf = Global_CmdLine()
		gconf.prompt = "(config)" + self.prompt
		gconf.cmdloop()
		
    def do_show(self, args):
		" Show running system information "
		sys.stdout.write('Running Show\n')
		
    def do_quit(self, args):
		" Quiting FlexSwitch CLI"
		sys.stdout.write('Quiting Shell\n')
		sys.exit(0)	
		
    def do_exit(self, args):
		" Quiting FlexSwitch CLI"
		sys.stdout.write('Exiting Shell\n')
		sys.exit(0)	
		
    def do_end(self, args):
        " Return to enable mode"
    	self.prompt = "#"
    	
    def do_shell(self, args):
       sys.stdout.write("")
        
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
		intconf.prompt = self.prompt[0:7] + "-if)"
		intconf.cmdloop()

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
    	return True and 1
    	#cmdLine = CmdLine()
    	#cmdLine.cmdloop()
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
