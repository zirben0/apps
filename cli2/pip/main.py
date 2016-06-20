import sys, os
from optparse import OptionParser
from snap_cli import CmdLine

# *** MAIN LOOP ***
def main():
    path = os.path.dirname(os.path.realpath(__file__))
    parser = OptionParser()
    parser.add_option("-s", "--switch", action="store", dest="switch_ip", type="string",
                      help="Switch IP to run the cli against", default= '127.0.0.1')
    parser.add_option("-m", "--model", action="store",type="string",
                      dest="cli_model_path",
                      help="Path to the cli model to be used",
                      default= '%s/models/cisco/'%(path))
    parser.add_option("-j", "--jschema", action="store",type="string",
                      dest="cli_schema_path",
                      help="Path to the cli model to be used",
                      default='%s/schema/'%(path))
    (options, args) = parser.parse_args()

    switch_ip='127.0.0.1'
    switch_ip = options.switch_ip
    cli_model_path = options.cli_model_path
    cli_schema_path = options.cli_schema_path
    print 'model path : ', cli_model_path
    print 'schema path: ', cli_schema_path 

    cmdLine = CmdLine(switch_ip, cli_model_path, cli_schema_path, )
    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #result = sock.connect_ex((switch_ip,8080))
    result = True
    if result:
        cmdLine.cmdloop()
    else:
        print "FlexSwitch not reachable, Please ensure daemon is up."
        sys.exit(2)


