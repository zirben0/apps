#!/usr/bin/python
#
#Copyright [2016] [SnapRoute Inc]
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#       Unless required by applicable law or agreed to in writing, software
#       distributed under the License is distributed on an "AS IS" BASIS,
#       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#       See the License for the specific language governing permissions and
#       limitations under the License.
#
# _______  __       __________   ___      _______.____    __    ____  __  .___________.  ______  __    __
# |   ____||  |     |   ____\  \ /  /     /       |\   \  /  \  /   / |  | |           | /      ||  |  |  |
# |  |__   |  |     |  |__   \  V  /     |   (----` \   \/    \/   /  |  | `---|  |----`|  ,----'|  |__|  |
# |   __|  |  |     |   __|   >   <       \   \      \            /   |  |     |  |     |  |     |   __   |
# |  |     |  `----.|  |____ /  .  \  .----)   |      \    /\    /    |  |     |  |     |  `----.|  |  |  |
# |__|     |_______||_______/__/ \__\ |_______/        \__/  \__/     |__|     |__|      \______||__|  |__|
#
# Main routine for the cli, will contain root node functionality within the cli tree
# Will be the container for the reference to the flexSdk and flexPrint, as well
# as holds the master model and schema for the cli.   The Cli utilizes a class cmdln.py which
# was built as a wrapper above the common cmd class as part of the standard python library as of 2.7
#

import sys, getopt, socket, os
import jsonref
import rlcompleter
import glob
import shutil
import time
import requests
import snapcliconst
from collections import Counter
from itertools import izip_longest
from optparse import OptionParser
from jsonschema import Draft4Validator

#from snap_global import Global_CmdLine
from snap_config import ConfigCmd
from snap_show import ShowCmd
from commonCmdLine import CommonCmdLine, CmdFunc, \
    SUBCOMMAND_VALUE_NOT_EXPECTED, SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE, SUBCOMMAND_VALUE_EXPECTED

class CmdLine(CommonCmdLine):

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
        self.privilege = False
        self.tmp_remove_priveledge = None
        self.IntfRefToIfIndex = {}
        self.IfIndexToIntfRef = {}
        # defaulting to show as it will be overwritten by the first config command
        self.cmdtype = snapcliconst.COMMAND_TYPE_INIT

        # check if we can reach the switch_ip will timeout if we can't
        if self.check_switch_connectivity(switch_ip, 8080):
            while not self.waitForSystemToBeReady():
                time.sleep(1)

            self.do_reload_cli_model([])
            self.setBanner(switch_ip)
        else:
            self.do_exit([])

    def check_switch_connectivity(self, switch_ip, port):
        """
        Function to check if we can reach the switch we are trying to connect to
        :param switch_ip:
        :param port:
        :return:
        """
        try:
            response=requests.get("http://%s:%s" %(switch_ip, str(port)), timeout=1)
            if response.status_code < 400 or response.status_code == 404:
                return True
            else:
                sys.stdout.write("ERROR: Unable to connect to system status %s\n" %(response.status_code))
                return False
        except Exception as e:
            sys.stdout.write("ERROR: Unable to connect to system: \n%s\n" %(e.message,))
            return False

    def setupcommands(self, teardown=False):

        # keep track of each of the commands being added as we will use
        # this list to add the aliases
        cmdNameList = []
        # this loop will setup each of the cliname commands for this model level
        for subcmds, cmd in self.model["commands"].iteritems():
            # handle the links
            if 'subcmd' in subcmds:
                try:
                    for k,v in cmd.iteritems():
                        cmdname = self.getCliName(v)
                        if '-' in cmdname:
                            sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                            self.do_exit([])
                            cmdname = cmdname.replace('-', '_')

                        cmdNameList.append(cmdname)
                        funcname = "do_" + cmdname
                        if not teardown:
                            setattr(self.__class__, funcname, CmdFunc(self, funcname, getattr(self, "_cmd_%s" %(k,))))
                            if hasattr(self.__class__, "_cmd_complete_%s" %(k,)):
                                setattr(self.__class__, "complete_" + cmdname, getattr(self, "_cmd_complete_%s" %(k,)))
                        else:
                            delattr(self.__class__, funcname)
                            if hasattr(self.__class__, funcname):
                                delattr(self.__class__, "complete_" + cmdname)
                except Exception as e:
                    sys.stdout.write("EXCEPTION RAISED on setting do_: %s\n" %(e,))
            else:
                # handle commands when are not links
                try:
                    cmdname = self.getCliName(self.model["commands"][subcmds])
                    if '-' in cmdname:
                        sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                        self.do_exit([])
                        cmdname = cmdname.replace('-', '_')

                    cmdNameList.append(cmdname)
                    funcname = "do_" + cmdname
                    if not teardown:
                        setattr(self.__class__, funcname, CmdFunc(self, funcname, getattr(self, "_cmd_%s" %(subcmds,))))
                    else:
                        delattr(self.__class__, funcname)
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED on setting do_: %s\n" %(e,))

        if not teardown:
            self.setupalias(cmdNameList)

    def teardowncommands(self):
        self.setupcommands(teardown=True)

    def isSystemReady(self):
        return self.check_switch_connectivity(self.switch_ip, 8080) and self.waitForSystemToBeReady()

    def waitForSystemToBeReady (self) :

        #typically we will allow for system to be ready if confd and sysd are ready
        # we know sysd is ready by the successful retrieval of SystemStatus
        # so we just need to check that confd is up
        requiredDaemons = ['confd',]
        try:
            r = self.sdk.getSystemStatusState("")
        except requests.exceptions.ConnectionError:
            sys.stdout.write("Unable to connect to system, flexswitch confd may not be up yet.\n")
            return False

        if r.status_code in self.sdk.httpSuccessCodes:
            resp = r.json()
            #for x in resp['Object']['FlexDaemons']:
            #    print x['Name'], x['State']
            if resp['Object']['Ready'] == True or \
                len(frozenset(requiredDaemons).intersection([x.get('Name', None) for x in resp['Object']['FlexDaemons'] if str(x.get('State', 'down')) == 'up'])) == 1:
                #sys.stdout.write('System Is ready\n')
                return True
            else:
                sys.stdout.write('System Is not ready yet\n')
                return False
        return False

    def setBanner(self, switch_ip):

        self.intro = " _______  __       __________   ___      _______.____    __    ____  __  .___________.  ______  __    __\n" \
                     "|   ____||  |     |   ____\  \ /  /     /       |\   \  /  \  /   / |  | |           | /      ||  |  |  |\n" \
                     "|  |__   |  |     |  |__   \  V  /     |   (----` \   \/    \/   /  |  | `---|  |----`|  ,----'|  |__|  |\n" \
                     "|   __|  |  |     |   __|   >   <       \   \      \            /   |  |     |  |     |  |     |   __   |\n" \
                     "|  |     |  `----.|  |____ /  .  \  .----)   |      \    /\    /    |  |     |  |     |  `----.|  |  |  |\n" \
                     "|__|     |_______||_______/__/ \__\ |_______/        \__/  \__/     |__|     |__|      \______||__|  |__|\n"
        self.intro +="                                _______  __       __ \n" \
                     "                               /       ||  |     |  |\n" \
                     "                              |   ,----||  |     |  |\n" \
                     "                              |   |     |  |     |  |\n" \
                     "                              |   `----.|  `----.|  |\n" \
                     "                               \_______||_______||__|\n"
        
        cliversion = "unknown"
        switchversion = "unknown"
        if 'properties' in self.schema and \
            'cli-version' in self.schema['properties']:
            cliversion = self.schema['properties']['cli-version']['default']
            r = self.sdk.getSystemSwVersionState("")
            if r.status_code in self.sdk.httpSuccessCodes:
                obj = r.json()
                o = obj['Object']
                switchversion = o['FlexswitchVersion']

        self.intro += "\nFlexSwitch Console Version %s, Connected to: %s Version %s" %(cliversion, self.switch_name, switchversion)
        self.intro += "\nUsing %s style cli\n" %(self.model["style"],)

    def discoverPortInfo(self):
        """
        Get all the ports in the system and store the IntfRef and IfIndex mappings
        :return:
        """
        ports = self.sdk.getAllPorts()
        for port in ports:
            p = port['Object']
            ifIndex = p['IfIndex']
            intfRef = p['IntfRef']
            self.IfIndexToIntfRef[ifIndex] = intfRef
            self.IntfRefToIfIndex[intfRef] = ifIndex

    def do_show_cli(self, arv):
        """Show all commands available within the CLI"""
        def submcmd_walk(subcmd):
            if type(subcmd) in (dict, jsonref.JsonRef):
                for k, v in subcmd.iteritems():
                    currcmdline = ''
                    if type(v) in (dict, jsonref.JsonRef):
                        if 'cliname' in v:
                            currcmdline += ' ' + v['cliname']
                        if 'commands' in v:
                            for kk, vv in v['commands'].iteritems():
                                if 'subcmd' in kk:
                                    for x in  submcmd_walk(vv):
                                        newcmdline = currcmdline + x
                                        yield newcmdline
                                elif type(vv) in (dict, jsonref.JsonRef):
                                    for kkk, vvv in vv.iteritems():
                                        if 'cliname' in kkk:
                                            newcmdline = currcmdline + vvv
                                            yield newcmdline
                        else:
                            # reached the attributes
                            for kk, vv in v.iteritems():
                                if 'cliname' in vv:
                                    newcmdline = currcmdline + ' ' + vv['cliname']
                                    yield newcmdline
            yield ''

        cmdList = []
        for k, v in self.model.iteritems():
            if "commands" == k:
                for kk, vv in v.iteritems():
                    cmdline = ''
                    if 'subcmd' in kk:
                        #traverse the commands
                        for x in submcmd_walk(vv):
                            cmdline = x
                            if cmdline not in cmdList:
                                cmdList.append(cmdline)
                    else:
                        for kkk, vvv in vv.iteritems():
                            if 'cliname' in kkk:
                                cmdline = vvv
                                if cmdline not in cmdList:
                                    cmdList.append(cmdline)
        for x in cmdList:
            sys.stdout.write("%s\n" %(x))


    def replace_cli_name(self, name, newname):
        '''
        The cli supports replacing any attribute with another.  This is mainly used
        to replace the ethernet keyword with the prefix used to describe ports
        :param name: name looking for in model
        :param newname: name to replace 'name' with
        :return:
        '''
        def submcmd_walk(name, newname, subcmd):
            if type(subcmd) in (dict, jsonref.JsonRef):
                for k, v in subcmd.iteritems():
                    if type(v) in (dict, jsonref.JsonRef):
                        if 'cliname' in v and v['cliname'] == name:
                            v['cliname'] = newname

                        if 'value' in v:
                            # reached the attributes
                            for kk, vv in v['value'].iteritems():
                                if 'cliname' in vv and vv['cliname'] == name:
                                    vv['cliname'] = newname

                        if 'commands' in v:
                            for kk, vv in v['commands'].iteritems():
                                if 'subcmd' in kk:
                                    submcmd_walk(name, newname, vv)
                                elif type(vv) in (dict, jsonref.JsonRef):
                                    for kkk, vvv in vv.iteritems():
                                        if 'cliname' in kkk and vvv == name:
                                            vv[kkk] = name

                        else:
                            # reached the attributes
                            for kk, vv in v.iteritems():
                                if 'cliname' in vv and vv['cliname'] == name:
                                    vv['cliname'] = newname

        for k, v in self.model.iteritems():
            if "commands" == k:
                if type(v) in (dict, jsonref.JsonRef):
                    for kk, vv in v.iteritems():
                        if 'subcmd' in kk:
                            #traverse the commands
                            submcmd_walk(name, newname, vv)
                        elif type(vv) in (dict, jsonref.JsonRef):
                            for kkk, vvv in vv.iteritems():
                                if 'cliname' in kkk and vvv == name:
                                    vv[kkk] = newname

    def validateSchemaAndModel(self):

        def detect_port_prefix(strings):
            threshold = len(strings)
            prefix = []
            prefixes = []
            for chars in izip_longest(*strings, fillvalue=''):
                char, count = Counter(chars).most_common(1)[0]
                if count == 1 and len(strings) > 1:
                    break
                elif count < threshold:
                    if prefix:
                        prefixes.append((''.join(prefix), threshold))
                    threshold = count
                prefix.append(char)
            if prefix:
                prefixes.append((''.join(prefix), threshold))
            #print prefixes
            #print max([x[1] for x in prefixes])
            maxprefix = [y[0] for y in prefixes if y[1] == max([x[1] for x in prefixes])][0]
            return maxprefix if len(strings) > 1 else maxprefix[:-1]

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
                try:
                    # lets validate the model against the json schema
                    Draft4Validator(self.schema).validate(self.model)

                    # lets replace the key word ethernet with the discovered prefix from
                    # the snapos ports
                    sdk = self.getSdk()
                    ports = sdk.getAllPorts()
                    if ports:
                        snapcliconst.PORT_NAME_PREFIX = detect_port_prefix([p['Object']['IntfRef'] for p in ports])
                        # NOTE: it is a requirement that the model use a pre-set name 'ethernet' to
                        # describe physical ports
                        self.replace_cli_name('ethernet', snapcliconst.PORT_NAME_PREFIX)
                    else:
                        sys.stdout.write("Failed to find ports in system, was DB deleted?\n")
                        self.do_exit([])
                except jsonref.JsonRefError as e:
                    sys.stdout.write("ERROR Failed Model/Schema out of sync: %s\n" %(e.message))
                except Exception as e:
                    print e
                    sys.stdout.write("Failed to find port prefix exiting CLI, is switch %s accessable? %s\n" %(self.switch_name, e))
                    # not going to exit as we want to keep things running
                    #self.do_exit([])

                self.setPrompt()

                # flag to make sure output of walk is not put to stdout
            except Exception as e:
                print e
                return False
        return True

    def setPrompt(self, ):

        # set the prompt
        self.baseprompt = self.model["prompt-prefix"] + self.model["prompt"]
        self.prompt = self.model["prompt-prefix"] + self.model["prompt"]

    def cmdloop(self, intro=None):
        """
        Cmd Loop which will call cmdln loop listening for commands.  But there
        is some logic needed based on whether this is the first time we are
        entering this loop or not.
        :param intro: display the banner
        :return:
        """
        try:
            if self.start:
                self.start = False
                CommonCmdLine.cmdloop(self, intro=self.intro)
            else:
                CommonCmdLine.cmdloop(self, intro="")
        except KeyboardInterrupt:
            self.intro = '\n'
            self.cmdloop()

    # match for schema cmd object
    def _cmd_privilege(self, arg):
        """Enabled Privilege Mode"""
        self.privilege = True
        submodelList = self.getSubCommand("privilege", self.model["commands"])
        subschemaList = self.getSubCommand("privilege", self.schema["properties"]["commands"]["properties"])
        if submodelList and subschemaList and len(submodelList) == 1:
            for submodel, subschema in zip(submodelList, subschemaList):
                self.prompt = self.prompt[:-1] + self.getPrompt(submodel, subschema)
                self.baseprompt = self.prompt
                self.currentcmd = self.lastcmd
    _cmd_privilege.aliases = ["en", "ena"]

    # match for schema cmd object
    def _cmd_config(self, args):
        """Global configuration mode"""

        newargs = [self.find_func_cmd_alias(arg) for arg in args]
        self.cmdtype = snapcliconst.COMMAND_TYPE_CONFIG

        if self.privilege is False:
            sys.stdout.write("Must be in privilege mode to execute config\n")
            return

        if len(newargs) > 1:
            snapcliconst.printErrorValueCmd(1, newargs)
            return

        # get the submodule to be passed into config
        #schemaname = self.getSchemaCommandNameFromCliName(name, self.model)
        submodelList = self.getSubCommand(newargs[0], self.model["commands"])
        subschemaList = self.getSubCommand(newargs[0], self.schema["properties"]["commands"]["properties"])
        # there should only be one config entry
        if submodelList and subschemaList and len(submodelList) == 1:
            for submodel, subschema in zip(submodelList, subschemaList):
                configprompt = self.getPrompt(submodel[newargs[0]], subschema[newargs[0]])
                # setup the prompt accordingly
                self.prompt = self.prompt[:-1] + configprompt + self.prompt[-1]
                # stop the command loop for config as we will be running a new cmd loop
                self.stop = True
                # save off the current command
                prevcmd = self.currentcmd
                self.currentcmd = self.lastcmd

                self.teardowncommands()
                self.stop = True
                c = ConfigCmd("config", self, newargs[0], self.prompt, submodel, subschema)
                c.cmdloop()
                self.setupcommands()
                # clear the command if we return
                self.currentcmd = prevcmd
                # return prompt to the base of this class
                self.prompt = self.baseprompt
                if self.stop:
                    self.cmdloop()

    def _cmd_complete_show(self, text, line, begidx, endidx):
        #sys.stdout.write("\n%s line: %s text: %s %s\n" %(self.objname, line, text, not text))
        # remove spacing/tab
        self.cmdtype = snapcliconst.COMMAND_TYPE_SHOW
        mline = [x for x in line.split(' ') if x != '']
        mlineLength = len(mline)
        #sys.stdout.write("complete \ncommand %s objname %s\n\n" %(mline, self.objname))

        subcommands = self.get_show_complete_commands(mline)
        # lets remove any duplicates
        returncommands = list(frozenset(subcommands).difference(mline))
        #print text, returncommands, subcommands, "\n"
        if len(text) == 0 and len(returncommands) == len(subcommands):
            return returncommands

        # lets only get commands which are a partial of what was entered
        returncommands = [k for k in returncommands if k.startswith(text)]

        return returncommands

    def get_show_complete_commands(self, mline):
        # calling
        submodelList = self.getSubCommand("show", self.model["commands"])
        subschemaList = self.getSubCommand("show", self.schema["properties"]["commands"]["properties"], self.model["commands"])
        if submodelList and subschemaList:
            for submodel, subschema in zip(submodelList, subschemaList):
                c = ShowCmd(self, submodel, subschema)
                return [cmd for (cmd,help) in c.display_help(mline[1:], returnhelp=True)]
        return []



    def display_show_help(self, mline):
        submodelList = self.getSubCommand("show", self.model["commands"])
        subschemaList = self.getSubCommand("show", self.schema["properties"]["commands"]["properties"], self.model["commands"])
        if submodelList and subschemaList:
            for submodel, subschema in zip(submodelList, subschemaList):
                c = ShowCmd(self, submodel, subschema)
                c.display_help(mline[1:])


    def _cmd_show(self, argv):
        """ Show running system information """
        RUNNING_CONFIG = "running_config"
        newargs = [self.find_func_cmd_alias(arg) for arg in argv]
        mline = newargs
        self.cmdtype = snapcliconst.COMMAND_TYPE_SHOW
        mlineLength = len(mline)
        if mlineLength > 1:
            cmd = RUNNING_CONFIG
            if len(frozenset(
                    [cmd[:i+1] for i, ch in enumerate(cmd) if i+1 >= 2 and cmd[:i+1] != cmd]).intersection([mline[1]])):
                self.currentcmd = self.lastcmd
                # TODO subcmd1 hard coded below is BAD!!!! cause what if schema/model changes then this will not work
                c = ShowCmd(self, self.model['commands']['subcmd1'], self.schema['properties']['commands']['properties']['subcmd1'])
                c.show(mline, all=True)
                return
            else:
                submodelList = self.getSubCommand(mline[0], self.model["commands"])
                subschemaList = self.getSubCommand(mline[0], self.schema["properties"]["commands"]["properties"], self.model["commands"])
                if mlineLength > 0:
                    try:
                        for i in range(1, mlineLength):
                            for submodel, subschema in zip(submodelList, subschemaList):
                                schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], submodel)
                                submodelList = self.getSubCommand(mline[i],
                                                                  submodel[schemaname]["commands"])
                                subschemaList = self.getSubCommand(mline[i],
                                                                   subschema[schemaname]["properties"]["commands"]["properties"],
                                                                   submodel[schemaname]["commands"])
                                if submodelList and subschemaList:
                                    for submodel, subschema in zip(submodelList, subschemaList):
                                        (valueexpected, objname, keys, help, islist) = self.isValueExpected(mline[i], submodel, subschema)
                                        # we want to keep looping untill there are no more value commands
                                        if valueexpected != SUBCOMMAND_VALUE_NOT_EXPECTED:
                                            if i == mlineLength - 1:
                                                self.currentcmd = self.lastcmd
                                                c = ShowCmd(self, submodel, subschema)
                                                c.show(mline, all=True)
                                                self.currentcmd = []
                                            else:
                                                subcommands = self.getchildrencmds(mline[i], submodel, subschema)
                                                if mline[i+1] not in subcommands:
                                                    self.currentcmd = self.lastcmd
                                                    c = ShowCmd(self, submodel, subschema)
                                                    c.show(mline, all=False)
                                                    self.currentcmd = []
                                        elif i == mlineLength - 1:
                                            if "commands" not in submodel:
                                                for key, value in submodel.iteritems():
                                                    if 'cliname' in value and value['cliname'] == mline[i]:
                                                        self.currentcmd = self.lastcmd
                                                        c = ShowCmd(self, submodel, subschema)
                                                        c.show(mline, all=True)
                                                        self.currentcmd = []

                    except Exception:
                        pass

    def do_exit(self, args):
        """Exit current CLI tree position, if at base then will exit CLI"""
        #subcmd = self.getSubCommand("privilege", self.model["commands"])
        if self.privilege:
            self.privilege = False
            #docmd = 'do_%s' %(subcmd['cliname'])
            #setattr(self.__class__, docmd, self.tmp_remove_priveledge)
            sys.stdout.write('Exiting Privilege mode\n')
            self.setPrompt()
            if self.stop:
                self.cmdloop()

        else:
            sys.stdout.write('Quiting Shell\n')
            sys.exit(0)


    def precmd(self, argv):
        newargv = [self.find_func_cmd_alias(x) for x in argv]
        if len(newargv) > 1 and 'help' in newargv:
            if newargv[0] == snapcliconst.COMMAND_TYPE_SHOW:
                self.display_show_help(newargv)
                return ''
            elif newargv[0] == snapcliconst.COMMAND_TYPE_CONFIG:
                self.display_help(newargv)
                return ''
        if newargv and '!' in newargv[-1]:
            self.do_exit(newargv)
            return ''

        return newargv

    def do_help(self, argv):
        """Display help for current commands"""
        self.display_help(argv)

    do_help.aliases = ["?"]

    def do_reload_cli_model(self, argv):
        """Command to dynamically reload model.  Useful when wanting to change the cli while it is running, can only be run from base cli"""

        # lets make /tmp/snaproute/cli/ directory if it does not exist
        # if it does exist lets clean the directory
        # lets move all the json schema and model to a temporary
        # directory structure so that the jsonref can properly
        # parse the references
        # /tmp/snaproute/cli/models
        # /tmp/snaproute/cli/schema
        x = PrepareModel(self.basemodelpath, self.baseschemapath)
        x.Prepare()

        self.setSchema()
        self.setModel()

        # lets make sure the model is correct
        valid = self.validateSchemaAndModel()

        if not valid:
            sys.stdout.write("schema and model mismatch")
            sys.exit(0)

        self.discoverPortInfo()
        self.setupcommands()


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

    cmdLine = CmdLine(switch_ip, cli_model_path, cli_schema_path, )
    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #result = sock.connect_ex((switch_ip,8080))
    result = True
    if result:
        cmdLine.cmdloop()
    else:
        print "FlexSwitch not reachable, Please ensure daemon is up."
        sys.exit(2)

