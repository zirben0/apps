#!/usr/bin/python

import sys, getopt, socket
from snap_global import Global_CmdLine
from cmd import Cmd
import readline
import rlcompleter
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
        self.prompt = switch_ip +"#"
        try:
        	switch_name = socket.gethostbyname(switch_ip)
        except socket.gaierror:
        	switch_name = switch_ip
        self.intro = "FlexSwitch Console Version 1.0, Connected to: " + switch_name 
        self.commands = Commands(switch_ip)
        self.command_help = Command_help()
        #self.fs_info = FlexSwitch_info(switch_ip)
		
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
		gconf = Global_CmdLine(self,switch_ip)
		gconf.prompt = self.prompt[:-1] + "(config)#"
		gconf.cmdloop()
		
    
    def do_show(self, arg):
        " Show running system information "
        if "?" in self.lastcmd:
        	return 
        return self.commands.show_commands(arg)

    def complete_show(self, text, line, begidx, endidx):
		return self.commands.auto_show(text, line, begidx, endidx)

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
        
    def precmd(self, line):
        if line.strip() == 'help':
            sys.stdout.write('%s\n' % self.__doc__)
            return ''
        elif line.endswith('?'):
	    	self.command_help.show_help(line)
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

