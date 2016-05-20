#!/usr/bin/python

import sys, getopt, socket, os
import jsonref
import cmdln
import readline
import rlcompleter
import glob
import shutil
from optparse import OptionParser
from jsonschema import Draft4Validator
#from snap_global import Global_CmdLine
from snap_config import ConfigCmd
from snap_show import ShowCmd
from commonCmdLine import CommonCmdLine, USING_READLINE
from flexswitchV2 import FlexSwitch
from flexprint import FlexPrint
from sets import Set

class CmdFunc(object):
    def __init__(self, origfuncname, func):
        self.name = origfuncname
        self.func = func

        # lets save off the function attributes to the class
        # in case someone like cmdln access it (which it does)
        x = dir(func)
        y = dir(self.__class__)
        z = Set(x).difference(y)
        for attr in z:
            setattr(self, attr, func.__getattribute__(attr))

    # allow class to be called as a method
    def __call__(self, *args, **kwargs):
        self.func(*args, **kwargs)


class CmdLine(cmdln.Cmdln, CommonCmdLine):
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
    # name of schema and model
    name = 'base.json'
    objname = 'base'
    def __init__(self, switch_ip, model_path, schema_path):
        self.start = True
        CommonCmdLine.__init__(self, None, switch_ip, schema_path, model_path, self.name)
        cmdln.Cmdln.__init__(self)
        self.privilege = False
        self.tmp_remove_priveledge = None
        self.sdk = FlexSwitch(switch_ip, 8080)
        self.sdkshow = FlexPrint(switch_ip, 8080)

        # this loop will setup each of the cliname commands for this model level
        for subcmds, cmd in self.model["commands"].iteritems():
            # handle the links
            if 'subcmd' in subcmds:
                try:
                    for k,v in cmd.iteritems():
                        cmdname = self.getCliName(v)
                        funcname = "do_" + cmdname
                        setattr(self.__class__, funcname, CmdFunc(funcname, self.__getattribute__("_cmd_%s" %(k,))))
                        if hasattr(self.__class__, "_cmd_complete_%s" %(k,)):
                            setattr(self.__class__, "complete_" + cmdname, self.__getattribute__("_cmd_complete_%s" %(k,)))
                except Exception as e:
                    sys.stdout.write("EXCEPTION RAISED on setting do_: %s\n" %(e,))
            else:
                # handle commands when are not links
                try:
                    cmdname = self.getCliName(self.model["commands"][subcmds])
                    funcname = "do_" + cmdname
                    setattr(self.__class__, funcname, CmdFunc(funcname, self.__getattribute__("_cmd_%s" %(subcmds,))))
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED on setting do_: %s\n" %(e,))


        self.setBanner(switch_ip)

    def setBanner(self, switch_ip):

        self.intro = "FlexSwitch Console Version 1.0, Connected to: " + self.switch_name
        self.intro += "\nUsing %s style cli\n" %(self.model["style"],)

    def validateSchemaAndModel(self):
        if self.model is None or self.schema is None:
            sys.exit(2)
        else:
            try:
                try:
                    self.switch_name = socket.gethostbyname(self.switch_ip)
                except socket.gaierror:
                    self.switch_name = self.switch_ip

                # update to add the prompt prefix
                self.model["prompt-prefix"] = self.switch_name

                #with open(self.modelpath, 'w') as f:
                #    jsonref.dump(self.model, f, indent=2)
                #self.setModel()
                self.setPrompt()

                # lets validate the model against the json schema
                Draft4Validator(self.model, self.schema)

            except Exception as e:
                print e
                return False
        return True

    def setPrompt(self, ):

        # set the prompt
        self.baseprompt = self.model["prompt-prefix"] + self.model["prompt"]
        self.prompt = self.model["prompt-prefix"] + self.model["prompt"]

    def cmdloop(self, intro=None):
        try:
            if self.start:
                self.start = False
                cmdln.Cmdln.cmdloop(self, intro=self.intro)
            else:
                cmdln.Cmdln.cmdloop(self, intro="")
        except KeyboardInterrupt:
            self.intro = '\n'
            self.cmdloop()


    def emptyline(self):
        pass

    @cmdln.alias("en", "ena")
    # match for schema cmd object
    def _cmd_privilege(self, arg):
        self.privilege = True
        submodelList = self.getSubCommand("privilege", self.model["commands"])
        subschemaList = self.getSubCommand("privilege", self.schema["properties"]["commands"]["properties"])
        if submodelList and subschemaList and len(submodelList) == 1:
            for submodel, subschema in zip(submodelList, subschemaList):
                self.prompt = self.prompt[:-1] + self.getPrompt(submodel, subschema)
                self.baseprompt = self.prompt
                self.currentcmd = self.lastcmd
        self.cmdloop()

    def xdo_help(self, arg):
        doc_strings = [ (i[3:], getattr(self, i).__doc__)
            for i in dir(self) if i.startswith('do_') ]
        doc_strings = [ '  %s\t%s\n' % (i, j)
            for i, j in doc_strings if j is not None ]
        sys.stdout.write('%s\n' % ''.join(doc_strings))

    @cmdln.alias("conf t", "configure t", "configure term", "conf term", "configure terminal", "config t")
    # match for schema cmd object
    def _cmd_config(self, args):
        " Global configuration mode "

        if self.privilege is False:
            return

        functionNameAsString = sys._getframe().f_code.co_name
        name = functionNameAsString.split("_")[-1]
        # get the submodule to be passed into config
        submodelList = self.getSubCommand(name, self.model["commands"])
        subschemaList = self.getSubCommand(name, self.schema["properties"]["commands"]["properties"])
        # there should only be one config entry
        if submodelList and subschemaList and len(submodelList) == 1:
            for submodel, subschema in zip(submodelList, subschemaList):
                configprompt = self.getPrompt(submodel[name], subschema[name])
                # setup the prompt accordingly
                self.prompt = self.prompt[:-1] + configprompt + self.prompt[-1]
                # stop the command loop for config as we will be running a new cmd loop
                cmdln.Cmdln.stop = True
                # save off the current command
                prevcmd = self.currentcmd
                self.currentcmd = self.lastcmd

                c = ConfigCmd("config", self, name, self.prompt, submodel, subschema)
                c.cmdloop()
                # clear the command if we return
                self.currentcmd = prevcmd
                # return prompt to the base of this class
                self.prompt = self.baseprompt

    def _cmd_complete_show(self, text, line, begidx, endidx):
        #sys.stdout.write("\n%s line: %s text: %s %s\n" %(self.objname, line, text, not text))
        # remove spacing/tab
        mline = [x for x in line.split(' ') if x != '']
        mlineLength = len(mline)
        #sys.stdout.write("complete \ncommand %s objname %s\n\n" %(mline, self.objname))

        functionNameAsString = sys._getframe().f_code.co_name
        name = functionNameAsString.split("_")[-1]

        submodelList = self.getSubCommand(name, self.model["commands"])
        subschemaList = self.getSubCommand(name, self.schema["properties"]["commands"]["properties"])
        subcommands = []
        for submodel, subschema in zip(submodelList, subschemaList):

            subcommands += self.getchildrencmds(mline[0], submodel, subschema)
            #sys.stdout.write("complete cmd: %s\ncommand %s subcommands %s\n\n" %(submodelList, name, subcommands))
            # advance to next submodel and subschema
            for i in range(1, mlineLength):
                #sys.stdout.write("%s submodel %s\n\n i subschema %s\n\n subcommands %s mline %s\n\n" %(i, submodel, subschema, subcommands, mline[i-1]))
                if mline[i-1] in submodel:
                    subsubmodelList = self.getSubCommand(mline[i], submodel[mline[i-1]]["commands"])
                    if subsubmodelList:
                        subsubschemaList = self.getSubCommand(mline[i], subschema[mline[i-1]]["properties"]["commands"]["properties"])
                        for subsubmodel, subsubschema in zip(subsubmodelList, subsubschemaList):
                            #sys.stdout.write("\ncomplete:  10 %s mline[i-1] %s mline[i] %s subschema %s\n" %(i, mline[i-i], mline[i], subsubschema))
                            valueexpected = self.isValueExpected(mline[1], subsubschema)
                            if valueexpected:
                                self.commandLen = len(mline)
                                return []
                            else:
                                subcommands += self.getchildrencmds(mline[i], subsubmodel, subsubschema)

        # todo should look next command so that this is not 'sort of hard coded'
        # todo should to a getall at this point to get all of the interface types once a type is found
        #sys.stdout.write("3: subcommands: %s\n\n" %(subcommands,))

        # lets remove any duplicates
        returncommands = list(Set(subcommands).difference(mline))

        if len(text) == 0 and len(returncommands) == len(subcommands):
            #sys.stdout.write("just before return %s" %(returncommands))
            return returncommands
        #elif len(text) == 0:
        #    # todo get all values ?
        #    pass
        # lets only get commands which are a partial of what was entered
        returncommands = [k for k in returncommands if k.startswith(text)]

        return returncommands

    def _cmd_show(self, argv):
        " Show running system information "
        if "?" in self.lastcmd:
            return

        functionNameAsString = sys._getframe().f_code.co_name
        name = functionNameAsString.split("_")[-1]
        mline = argv
        mlineLength = len(mline)
        submodelList = self.getSubCommand(name, self.model["commands"])
        subschemaList = self.getSubCommand(name, self.schema["properties"]["commands"]["properties"])
        if mlineLength > 0:
            try:
                for i in range(1, mlineLength):
                    for submodel, subschema in zip(submodelList, subschemaList):
                        if mline[i-1] in submodel:
                            submodelList = self.getSubCommand(mline[i], submodel[mline[i-1]]["commands"])
                            if submodelList:
                                subschemaList = self.getSubCommand(mline[i], subschema[mline[i-1]]["properties"]["commands"]["properties"])
                                for submodel, subschema in zip(submodelList, subschemaList):
                                    valueexpected = self.isValueExpected(mline[i], subschema)
                                    if valueexpected:
                                        self.currentcmd = self.lastcmd
                                        c = ShowCmd(self, [submodel], [subschema])
                                        c.show(mline, all=(i == mlineLength-1))
                                        self.currentcmd = []

            except Exception:
                pass

        self.cmdloop()

    def do_exit(self, args):
        " Quiting FlexSwitch CLI"
        #subcmd = self.getSubCommand("privilege", self.model["commands"])
        if self.privilege:
            self.privilege = False
            #docmd = 'do_%s' %(subcmd['cliname'])
            #setattr(self.__class__, docmd, self.tmp_remove_priveledge)
            sys.stdout.write('Exiting Privilege mode\n')
            self.setPrompt()
            self.cmdloop()

        else:
            sys.stdout.write('Quiting Shell\n')
            sys.exit(0)

class PrepareModel(object):
    def __init__(self, cli_model_path, cli_schema_path):
        # path location on the local drive where the cli model is located
        self.model_path = cli_model_path
        # path location on the local drive where the cli schema is located
        self.schema_path = cli_schema_path
        # path where model ref's will live
        self.ref_model_path = '/tmp/snaproute/cli/model/' + cli_model_path.split('/')[-2] + '/'
        # path where schema ref's will live
        self.ref_schema_path = '/tmp/snaproute/cli/schema/'

    def Prepare(self):
        # create the directories if they don't already exist
        # if it exists function will remove existing files
        self.mkdir_p(self.ref_model_path)
        self.mkdir_p(self.ref_schema_path)

        self.copy_json_to_new_path(self.model_path, self.ref_model_path)
        self.copy_json_to_new_path(self.schema_path, self.ref_schema_path)

    def mkdir_p(self, path):

        # lets clean the directory if it exists in case other models exist
        try:
            shutil.rmtree(path)
        except Exception:
            pass

        if not os.access(path, os.F_OK):
            os.makedirs(path)

    def copy_json_to_new_path(self, oldpath, newpath):

        for filename in glob.glob(os.path.join(oldpath, '*.json')):
            #sys.stdout.write("copying file:%s to %s\n" %(filename, newpath))
            try:
                shutil.copy(filename, newpath)
            except IOError:
                pass



# *** MAIN LOOP ***
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-s", "--switch", action="store", dest="switch_ip", type="string",
                      help="Switch IP to run the cli against", default= '127.0.0.1')
    parser.add_option("-m", "--model", action="store",type="string",
                      dest="cli_model_path",
                      help="Path to the cli model to be used",
                      default= './models/cisco/')
    parser.add_option("-j", "--jschema", action="store",type="string",
                      dest="cli_schema_path",
                      help="Path to the cli model to be used",
                      default='./schema/')
    (options, args) = parser.parse_args()

    switch_ip='127.0.0.1'
    switch_ip = options.switch_ip
    cli_model_path = options.cli_model_path
    cli_schema_path = options.cli_schema_path

    # lets make /tmp/snaproute/cli/ directory if it does not exist
    # if it does exist lets clean the directory
    # lets move all the json schema and model to a temporary
    # directory structure so that the jsonref can properly
    # parse the references
    # /tmp/snaproute/cli/models
    # /tmp/snaproute/cli/schema
    x = PrepareModel(cli_model_path, cli_schema_path)
    x.Prepare()


    cmdLine = CmdLine(switch_ip, cli_model_path, cli_schema_path, )
    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #result = sock.connect_ex((switch_ip,8080))
    result = True
    if result:
        cmdLine.cmdloop()
    else:
        print "FlexSwitch not reachable, Please ensure daemon is up."
        sys.exit(2)

