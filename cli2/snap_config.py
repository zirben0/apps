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
#
# Class handles initial config command
#
import sys
from sets import Set
import cmdln
import json
import pprint
import inspect
import string
import snapcliconst
from jsonref import JsonRef
from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine, SUBCOMMAND_VALUE_NOT_EXPECTED, \
    SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE, SUBCOMMAND_VALUE_EXPECTED
from snap_leaf import LeafCmd
from cmdEntry import *

try:
    from flexswitchV2 import FlexSwitch
    MODELS_DIR = './'
except:
    sys.path.append('/opt/flexswitch/sdk/py/')
    MODELS_DIR='/opt/flexswitch/models/'
    from flexswitchV2 import FlexSwitch

pp = pprint.PrettyPrinter(indent=2)
class ConfigCmd(cmdln.Cmdln, CommonCmdLine):

    def __init__(self, cmdtype, parent, objname, prompt, model, schema):
        '''

        :param cmdtype: 'show','config','delete' (implies config as well)
        :param parent: caller
        :param objname: name of this object
        :param prompt: parent prompt
        :param model: (model - callers layer)
        :param schema: (schema - callers layer)
        :return:
        '''

        cmdln.Cmdln.__init__(self)
        self.objname = objname
        self.name = objname + ".json"
        self.parent = parent
        self.model = model
        self.schema = schema
        self.baseprompt = prompt
        self.prompt = self.baseprompt
        self.commandLen = 0
        self.currentcmd = []
        self.cmdtype = cmdtype
        #store all the pending configuration objects
        self.configList = []
        self.valueexpected = SUBCOMMAND_VALUE_NOT_EXPECTED

        self.setupCommands()

        sys.stdout.write("\n*** Configuration will only be applied once 'apply' command is entered ***\n\n")

    def setupCommands(self):
        '''
        This api will setup all the do_<command> and comlete_<command> as required by the cmdln class.
        The functionality is common for all commands so we will map the commands based on what is in
        the model.
        :return:
        '''
        # this loop will setup each of the cliname commands for this model level
        # cmdln/cmd expects that all commands have a function associated with it
        # in the format of 'do_<command>'
        # TODO need to add support for when the cli mode does not supply the cliname
        #      in this case need to get the default from the schema model
        # this loop will setup each of the cliname commands for this model level
        ignoreKeys = []
        if self.objname in self.schema and \
            'properties' in self.schema[self.objname] and \
                'value' in self.schema[self.objname]['properties'] and \
                    'properties' in self.schema[self.objname]['properties']['value']:
            ignoreKeys = self.schema[self.objname]['properties']['value']['properties'].keys()

        for subcmds, cmd in self.model[self.objname]["commands"].iteritems():
            # handle the links
            if 'subcmd' in subcmds:
                try:
                    for k,v in cmd.iteritems():
                        # don't add the base key
                        if k not in ignoreKeys:
                            cmdname = self.getCliName(v)
                            if '-' in cmdname:
                                sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                                self.do_exit([])
                                cmdname = cmdname.replace('-', '_')

                            setattr(self.__class__, "do_" + cmdname, self._cmd_common)
                            setattr(self.__class__, "complete_" + cmdname, self._cmd_complete_common)
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED: %s" %(e,))
            else:
                # handle commands when are not links
                try:
                    cmdname = self.getCliName(self.model[self.objname][subcmds])
                    if '-' in cmdname:
                        sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                        self.do_exit([])
                        cmdname = cmdname.replace('-', '_')

                    setattr(self.__class__, "do_" + cmdname, self._cmd_common)
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED: %s" %(e,))

        setattr(self.__class__, "do_no", self._cmd_do_delete)
        setattr(self.__class__, "complete_no", self._cmd_complete_delete)

    def teardownCommands(self):
        '''
        This api will setup all the do_<command> and comlete_<command> as required by the cmdln class.
        The functionality is common for all commands so we will map the commands based on what is in
        the model.
        :return:
        '''
        # this loop will setup each of the cliname commands for this model level
        # cmdln/cmd expects that all commands have a function associated with it
        # in the format of 'do_<command>'
        # TODO need to add support for when the cli mode does not supply the cliname
        #      in this case need to get the default from the schema model
        # this loop will setup each of the cliname commands for this model level
        for subcmds, cmd in self.model[self.objname]["commands"].iteritems():
            # handle the links
            if 'subcmd' in subcmds:
                try:
                    for k,v in cmd.iteritems():
                        cmdname = self.getCliName(v)
                        if '-' in cmdname:
                            sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                            self.do_exit([])
                            cmdname = cmdname.replace('-', '_')

                        delattr(self.__class__, "do_" + cmdname)
                        delattr(self.__class__, "complete_" + cmdname)
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED: %s" %(e,))
            else:
                # handle commands when are not links
                try:
                    cmdname = self.getCliName(self.model[self.objname][subcmds])
                    if '-' in cmdname:
                        sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                        self.do_exit([])
                        cmdname = cmdname.replace('-', '_')

                    delattr(self.__class__, "do_" + cmdname)
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED: %s" %(e,))

        delattr(self.__class__, "do_no")
        delattr(self.__class__, "complete_no")


    def cmdloop(self, intro=None):
        cmdln.Cmdln.cmdloop(self)

    def _cmd_complete_delete(self, text, line, begidx, endidx):
        #sys.stdout.write("\n%s line: %s text: %s %s\n" %('no ' + self.objname, line, text, not text))
        mline = [x for x in line.split(' ') if x != '']
        mline = mline[1:]
        #sys.stdout.write("\n%s mline %s\n" %('no ' + self.objname, mline))

        return self._cmd_complete_common(text, ' '.join(mline), begidx, endidx)

    def _cmd_do_delete(self, argv):

        self.cmdtype = snapcliconst.COMMAND_TYPE_DELETE
        self._cmd_common(argv[1:])

    def _cmd_complete_common(self, text, line, begidx, endidx):

        #sys.stdout.write("\n%s line: %s text: %s %s\n" %(self.objname, line, text, not text))
        # remove spacing/tab
        mline = [self.objname] + [x for x in line.split(' ') if x != '']
        mlineLength = len(mline)
        #sys.stdout.write("complete cmd: %s\ncommand %s objname %s\n\n" %(self.model, mline[0], self.objname))

        submodel = self.model
        subschema = self.schema

        subcommands = []
        if len(mline) == 1:
            for f in dir(self.__class__):
                if f.startswith('do_') and not f.endswith('no'):
                    subcommands.append(f.lstrip('do_'))

        # advance to next submodel and subschema
        for i in range(1, mlineLength):
            #sys.stdout.write("%s submodel %s\n\n i subschema %s\n\n subcommands %s mline %s\n\n" %(i, submodel, subschema, subcommands, mline[i-1]))
            if mline[i-1] in submodel:
                schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], submodel)
                #sys.stdout.write("config complete: mline[i]=%s schemaname %s\n" %(mline[i], schemaname))
                if schemaname:
                    submodelList = self.getSubCommand(mline[i], submodel[schemaname]["commands"])
                    #sys.stdout.write("config complete: submodel[schemaname][commands] = %s\n" %(submodel[schemaname]["commands"]))
                    if submodelList:
                        subschemaList = self.getSubCommand(mline[i], subschema[schemaname]["properties"]["commands"]["properties"], model=submodel[schemaname]["commands"])
                        for submodel, subschema in zip(submodelList, subschemaList):
                            #sys.stdout.write("\ncomplete:  10 %s mline[i-1] %s mline[i] %s model %s\n" %(i, mline[i-i], mline[i], submodel))
                            (valueexpected, objname, keys, help) = self.isValueExpected(mline[i], submodel, subschema)
                            #sys.stdout.write("valueexpeded %s, objname %s, keys %s, help %s\n" %(valueexpected, objname, keys, help))
                            if valueexpected != SUBCOMMAND_VALUE_NOT_EXPECTED:
                                if valueexpected == SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE:
                                    values = self.getCommandValues(objname, keys)
                                    if not values:
                                        values = self.getValueSelections(mline[i], submodel, subschema)
                                    return values
                            else:
                                subcommands += self.getchildrencmds(mline[i], submodel, subschema)

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

    def _cmd_common(self, argv):
        # each config command takes a cmd, subcmd and value
        # example: interface ethernet <port#>
        #          vlan <vlan #>
        if len(argv) != self.commandLen:
            if self.stop:
                self.cmdloop()
            else:
                return
        # reset the command len
        self.commandLen = 0
        endprompt = ''
        # should be at config x
        schemaname = self.getSchemaCommandNameFromCliName(self.objname, self.model)
        if schemaname:
            submodelList = self.getSubCommand(argv[0], self.model[schemaname]["commands"])
            subschemaList = self.getSubCommand(argv[0], self.schema[schemaname]["properties"]["commands"]["properties"], self.model[schemaname]["commands"])
            schemaname = self.getSchemaCommandNameFromCliName(argv[0], submodelList[0])
            if schemaname:
                configprompt = self.getPrompt(submodelList[0][schemaname], subschemaList[0][schemaname])
                if snapcliconst.COMMAND_TYPE_DELETE not in self.cmdtype and configprompt:
                    endprompt = self.baseprompt[-2:]
                    self.prompt = self.baseprompt[:-2] + '-' + configprompt + '-'

                value = None
                objname = schemaname
                for i in range(1, len(argv)-1):
                    for submodel, subschema in zip(submodelList, subschemaList):
                        schemaname = self.getSchemaCommandNameFromCliName(argv[i-1], submodel)
                        if schemaname:
                            submodelList, subschemaList = self.getSubCommand(argv[i], submodel[schemaname]["commands"]), \
                                                            self.getSubCommand(argv[i], subschema[schemaname]["properties"]["commands"]["properties"], submodel[schemaname]["commands"])
                            if submodelList and subschemaList:
                                for submodel, subschema in zip(submodelList, subschemaList):
                                    schemaname = self.getSchemaCommandNameFromCliName(argv[i], submodel)
                                    if schemaname:
                                        configprompt = self.getPrompt(submodel[schemaname], subschema[schemaname])
                                        objname = schemaname
                                        if configprompt and snapcliconst.COMMAND_TYPE_DELETE not in self.cmdtype:
                                            if not endprompt:
                                                endprompt = self.baseprompt[-2:]
                                                self.prompt = self.baseprompt[:-2] + '-'

                                            self.prompt += configprompt + '-'
                                            value = argv[-1]

                if value != None:
                    self.prompt += value + endprompt
                elif snapcliconst.COMMAND_TYPE_DELETE not in self.cmdtype and self.prompt[:-1] != "#":
                    self.prompt = self.prompt[:-1] + endprompt
                self.stop = True
                prevcmd = self.currentcmd
                self.currentcmd = self.lastcmd
                # stop the command loop for config as we will be running a new cmd loop
                cmdln.Cmdln.stop = True

                # this code was added to handle admin state changes for global objects
                # bfd enable
                cliname = argv[-2]
                if self.valueexpected == SUBCOMMAND_VALUE_EXPECTED:
                    self.cmdtype += snapcliconst.COMMAND_TYPE_CONFIG_NOW
                    cliname = argv[-1]

                self.teardownCommands()
                c = LeafCmd(objname, cliname, self.cmdtype, self, self.prompt, submodelList, subschemaList)
                if c.applybaseconfig(cliname):
                    c.cmdloop()
                self.setupCommands()

                self.cmdtype = self.cmdtype.rstrip(snapcliconst.COMMAND_TYPE_CONFIG_NOW)
                if snapcliconst.COMMAND_TYPE_DELETE in self.cmdtype:
                    self.cmdtype = snapcliconst.COMMAND_TYPE_CONFIG

                self.prompt = self.baseprompt
                self.currentcmd = prevcmd
                # lets clear the config
                delconfigList = []
                for config in self.configList:
                    if not config.isPending():
                        config.clear(None, None, all=True)
                        if config.isEntryEmpty():
                            delconfigList.append(config)

                for delconfig in delconfigList:
                    self.configList.remove(delconfig)

        if self.stop:
            self.cmdloop()

    def precmd(self, argv):

        mlineLength = len(argv) - (1 if 'no' in argv else 0)
        parentcmd = self.parent.lastcmd[-2] if len(self.parent.lastcmd) > 1 else self.parent.lastcmd[-1]
        mline = [parentcmd] + [x for x in argv if x != 'no']
        subschema = self.schema
        submodel = self.model
        subcommands = []
        if mlineLength > 0:

            cmd = argv[-1]
            if cmd in ('?', ) and cmd not in ('exit', 'end', 'help', 'no', '!'):
                self.display_help(argv)
                return ''
            if cmd in ('!',):
                self.do_exit(argv)
                return ''

            self.commandLen = 0
            try:
                for i in range(1, len(mline)):
                    schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], submodel)
                    if schemaname:
                        submodelList = self.getSubCommand(mline[i], submodel[schemaname]["commands"])
                        subschemaList = self.getSubCommand(mline[i], subschema[schemaname]["properties"]["commands"]["properties"], submodel[schemaname]["commands"])
                        if submodelList and subschemaList:
                            for submodel, subschema in zip(submodelList, subschemaList):
                                subcommands += self.getchildrencmds(mline[i], submodel, subschema)
                                (valueexpected, objname, keys, help) = self.isValueExpected(mline[i], submodel, subschema)
                                if valueexpected != SUBCOMMAND_VALUE_NOT_EXPECTED:
                                    #if mlineLength - i > 1:
                                    #    sys.stdout.write("Invalid command entered, ignoring\n")
                                    #    return ''
                                    if valueexpected == SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE:
                                        values = self.getValueSelections(mline[i], submodel, subschema)
                                        if i < mlineLength and values and mline[i+1] not in values:
                                            snapcliconst.printErrorValueCmd(i, mline)
                                            sys.stdout.write("\nERROR: Invalid Selection %s, must be one of %s\n" % (mline[i+1], ",".join(values)))
                                            return ''
                                        min,max = self.getValueMinMax(mline[i], submodel, subschema)
                                        if min is not None and max is not None:
                                            try:
                                                num = string.atoi(mline[i+1])
                                                if num < min or num > max:
                                                    snapcliconst.printErrorValueCmd(i, mline)
                                                    sys.stdout.write("\nERROR: Invalid Value %s, must be beteween %s-%s\n" % (mline[i+1], min, max))
                                                    return ''
                                            except:
                                                sys.stdout.write("\nERROR: Invalid Value %s, must be beteween %s-%s\n" % (mline[i+1], min, max))
                                                return ''

                                        #values = self.getCommandValues(objname, keys)
                                        #sys.stdout.write("FOUND values %s" %(values))
                                        self.commandLen = len(mline[:i]) + 1
                                    else:
                                        self.commandLen = len(mline[:i])
                                    self.valueexpected = valueexpected
                                elif i == mlineLength - 1 and mline[i+1] in subcommands:
                                    schemaname = self.getSchemaCommandNameFromCliName(mline[i], submodel)
                                    if schemaname:
                                        for (submodelkey, submodel), (subschemakey, subschema) in zip(submodel[schemaname]["commands"].iteritems(),
                                                                                                      subschema[schemaname]['properties']["commands"]["properties"].iteritems()):
                                            if 'subcmd' in submodelkey:
                                                if self.isCommandLeafAttrs(submodel, subschema):
                                                    #leaf attr model
                                                    (valueexpected, objname, keys, help) = self.isLeafValueExpected(mline[i+1], submodel, subschema)
                                                    if valueexpected != SUBCOMMAND_VALUE_NOT_EXPECTED:
                                                        if valueexpected == SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE:
                                                            self.commandLen = len(mline[:i]) + 2
                                                        else:
                                                            self.commandLen = len(mline[:i]) + 1
                                                    else:
                                                        self.commandLen = len(mline[:i])
                                                    self.valueexpected = valueexpected

            except Exception as e:
                sys.stdout.write("precmd: error %s" %(e,))
                pass

        return argv

    def do_router(self):
        pass

    def do_ip(self):
        pass

    def do_help(self, argv):
        self.display_help(argv)

    def do_exit(self, args):
        self.teardownCommands()
        self.prompt = self.baseprompt
        self.stop = True

    def get_sdk_func_key_values(self, data, func):
        argspec = inspect.getargspec(func)
        getKeys = argspec.args[1:]
        lengthkwargs = len(argspec.defaults) if argspec.defaults is not None else 0
        if lengthkwargs > 0:
            getKeys = argspec.args[:-len(argspec.defaults)]

        # lets setup the argument list
        # and remove the values from the kwargs
        argumentList = []
        # set all the args
        if 'create' in func.__name__ or \
           'get' in func.__name__ or \
           'delete' in func.__name__:
            for k in getKeys:
                if k in data:
                    argumentList.append(data[k])
                    if lengthkwargs > 0:
                        if k in data:
                            del data[k]

            if lengthkwargs == 0:
                data = {}
        elif 'update' in func.__name__:
            for k in getKeys:
                if k in data:
                    argumentList.append(data[k])
                    if k in data:
                        del data[k]

        return (argumentList, data)

    def doesConfigExist(self, c):
        '''
        :param entry: CmdEntry
        :return: already provisioned CmdEntry or None if it does not exist
        '''
        for config in self.configList:
            if config.name == c.name:
                # lets get a list of keys from the existing config object
                keyvalues = [x.get()[1:] for x in config.attrList if x.isKey() == True]
                for entry in c.attrList:
                    if entry.isKey() and entry.get()[1:] in keyvalues:
                        return config
        return None

    def convertKeyValueToDisplay(self, objName, key, value):
        #TODO this is a hack need a proper common mechanism to change special values
        returnval = value
        if key in snapcliconst.DYNAMIC_MODEL_ATTR_NAME_LIST:
            # lets strip the string name prepended
            returnval = returnval.replace(snapcliconst.PORT_NAME_PREFIX, "")
            # TODO not working when this is enabled so going have to look into this later
            #returnval = '1/' + returnval
        return returnval

    def getCommandValues(self, objname, keys):

        # get the sdk
        try:
            sdk = self.getSdk()
            funcObjName = objname
            getall_func = getattr(sdk, 'getAll' + funcObjName + 's')
            if getall_func:
                objs = getall_func()
                if objs:
                    return [self.convertKeyValueToDisplay(objname, keys[0], obj['Object'][keys[0]]) for obj in objs]
        except Exception as e:
            sys.stdout.write("CommandValues: FAILED TO GET OBJECT: %s key %s reason:%s\n" %(objname, keys, e,))

        return []

    def getConfigOrder(self, configList):
        '''
        It is important that we apply deletes before create in particular order.
        It is equally important that certain configuration be applied before others

        IMPORTANT to note that configOrder.json is manually created file so if more
        objects are added/deleted then this file needs to be updated.
        :param configList:
        :return:
        '''
        cfgorder = []
        delcfgorder = []
        with open(MODELS_DIR + 'configOrder.json', 'r') as f:
            cfgorder = json.load(f,)['Order']
            delcfgorder = list(reversed(cfgorder))

        # certain objects have a specific order that need to be configured in
        # but not all objects have a dependency.  Lets configure those objects
        # which are part of the dependency list then apply everything else
        attemptedApplyConfigList = []
        for objname in delcfgorder:
            for config in self.configList:
                if config.name == objname and config.delete:
                    attemptedApplyConfigList.append(config)
                    yield config

        for objname in cfgorder:
            for config in self.configList:
                if config.name == objname and not config.delete:
                    attemptedApplyConfigList.append(config)
                    yield config

        for config in self.configList:
            if config.delete and config not in attemptedApplyConfigList:
                attemptedApplyConfigList.remove(config)
                yield config

        for config in self.configList:
            if not config.delete and config not in attemptedApplyConfigList:
                yield config

        yield None

    def do_show(self, argv):
        root = self.getRootObj()
        if root:
            if hasattr(root, '_cmd_show'):
                root._cmd_show(argv)

    def do_apply(self, argv):
        PROCESS_CONFIG = 1
        ROLLBACK_CONFIG = 2
        ROLLBACK_UPDATE = 1
        ROLLBACK_CREATE = 2
        ROLLBACK_DELETE = 3

        root = self.getRootObj()

        if self.configList and \
                root.isSystemReady():

            sys.stdout.write("Applying Config:\n")
            clearAppliedList = []
            rollbackData = {}
            failurecfg = False
            for stage in (PROCESS_CONFIG, ROLLBACK_CONFIG):
                # if no failures occured then ignore rolling back config
                if stage == ROLLBACK_CONFIG:
                    if not failurecfg:
                        continue
                    else:
                        sys.stdout.write("*************CONFIG FAILED ROLLING BACK ANY SUCCESSFUL CONFIG*************\n")

                # apply delete config before create
                for config in self.getConfigOrder(self.configList):
                    # don't process other commands if any of them failed
                    # during second pass we will rollback the config
                    if config and config.isValid() and \
                            ((not failurecfg and stage == PROCESS_CONFIG) or
                             stage == ROLLBACK_CONFIG):

                        # get the sdk
                        sdk = self.getSdk()
                        funcObjName = config.name

                        #lets see if the object exists, by doing a get first
                        # the only case in which a function should not exist
                        # is if it is a sub attrbute.
                        if hasattr(sdk, 'get' + funcObjName):
                            get_func = getattr(sdk, 'get' + funcObjName)
                            update_func = getattr(sdk, 'update' + funcObjName)
                            create_func = getattr(sdk, 'create' + funcObjName)
                            delete_func = getattr(sdk, 'delete' + funcObjName)
                            try:
                                origData = None
                                if stage != ROLLBACK_CONFIG:
                                    data = config.getSdkConfig()
                                    (argumentList, kwargs) = self.get_sdk_func_key_values(data, get_func)
                                    # update all the arguments
                                    r = get_func(*argumentList)
                                    status_code = r.status_code
                                    if status_code not in sdk.httpSuccessCodes + [404]:
                                        sys.stdout.write("Command Get FAILED\n%s %s\n" %(r.status_code, r.json()['Error']))
                                        sys.stdout.write("sdk:%s(%s,%s)\n" %(get_func.__name__,
                                              ",".join(["%s" %(x) for x in argumentList]),
                                              ",".join(["%s=%s" %(x,y) for x,y in kwargs.iteritems()])))
                                    elif status_code not in [404]: # not found
                                        origData = r.json()['Object']
                                    elif status_code in [404] and config.delete:
                                        sys.stdout.write("Command Get FAILED\n%s %s\n" %(r.status_code, r.json()['Error']))
                                        sys.stdout.write("warning: nothing to delete invalidating command\n")
                                        sys.stdout.write("sdk:%s(%s,%s)\n" %(get_func.__name__,
                                              ",".join(["%s" %(x) for x in argumentList]),
                                              ",".join(["%s=%s" %(x,y) for x,y in kwargs.iteritems()])))
                                        clearAppliedList.append(config)
                                        continue
                                else:
                                    if config in rollbackData:
                                        status_code = rollbackData[config]
                                        origData = rollbackData[funcObjName][1]
                                    else:
                                        continue

                                if status_code in sdk.httpSuccessCodes + [ROLLBACK_UPDATE] and \
                                        not config.delete:
                                    # update
                                    (failurecfg, delList) = self.applyUpdateNodeConfig(sdk, config, update_func, origData, (stage == ROLLBACK_CONFIG))
                                    if not failurecfg and stage == PROCESS_CONFIG:
                                        clearAppliedList += delList
                                        rollbackData[config] = (ROLLBACK_UPDATE, origData)

                                elif status_code in (404, ROLLBACK_DELETE):
                                    # create
                                    (failurecfg, delList) = self.applyCreateNodeConfig(sdk, config, create_func)
                                    if not failurecfg and stage == PROCESS_CONFIG:
                                        clearAppliedList += delList
                                        rollbackData[config] = (ROLLBACK_CREATE, origData)

                                elif status_code in (ROLLBACK_CREATE,) or \
                                    config.delete:
                                    # delete
                                    (failurecfg, delList) = self.applyDeleteNodeConfig(sdk, config, delete_func)
                                    if not failurecfg and stage == PROCESS_CONFIG:
                                        clearAppliedList += delList
                                        rollbackData[config] = (ROLLBACK_DELETE, origData)

                            except Exception as e:
                                sys.stdout.write("FAILED TO GET OBJECT: %s\n" %(e,))

            if clearAppliedList:
                for config in clearAppliedList:
                    if config:
                        self.configList.remove(config)

    def applyCreateNodeConfig(self, sdk, config, create_func):
        failurecfg = False
        delconfigList = []
        data = config.getSdkConfig()
        (argumentList, kwargs) = self.get_sdk_func_key_values(data, create_func)
        if kwargs:
            r = create_func(*argumentList, **kwargs)
        else:
            r = create_func(*argumentList)
        if r.status_code not in (sdk.httpSuccessCodes) and ('exists' and 'Nothing to be updated') not in errorStr:
            sys.stdout.write("command create FAILED:\n%s %s\n" % (r.status_code, r.json()['Error']))
            failurecfg = True
        else:
            sys.stdout.write("create SUCCESS:   http status code: %s\n" % (r.status_code,))
            if r.json()['Error']:
                sys.stdout.write("warning return code: %s\n" % (r.json()['Error']))

            # set configuration to applied state
            config.setPending(False)
            config.show()
            delconfigList.append(config)
        sys.stdout.write("sdk:%s(%s,%s)\n" % (create_func.__name__,
                                              ",".join(["%s" % (x) for x in argumentList]),
                                              ",".join(["%s=%s" % (x, y) for x, y in kwargs.iteritems()])))
        return failurecfg, delconfigList

    def applyDeleteNodeConfig(self, sdk, config, delete_func):
        failurecfg = False
        delconfigList = []
        data = config.getSdkConfig()
        (argumentList, kwargs) = self.get_sdk_func_key_values(data, delete_func)
        if kwargs:
            r = delete_func(*argumentList, **kwargs)
        else:
            r = delete_func(*argumentList)
        if r.status_code not in (sdk.httpSuccessCodes + [410]) and ('exists' and 'Nothing to be updated') not in errorStr: # 410 - Done
            sys.stdout.write("command delete FAILED:\n%s %s\n" % (r.status_code, r.json()['Error']))
            failurecfg = True
        else:
            sys.stdout.write("delete SUCCESS:   http status code: %s\n" % (r.status_code,))
            if r.json()['Error']:
                sys.stdout.write("warning return code: %s\n" % (r.json()['Error']))

            # set configuration to applied state
            config.setPending(False)
            config.show()
            delconfigList.append(config)
        sys.stdout.write("sdk:%s(%s,%s)\n" % (delete_func.__name__,
                                              ",".join(["%s" % (x) for x in argumentList]),
                                              ",".join(["%s=%s" % (x, y) for x, y in kwargs.iteritems()])))
        return failurecfg, delconfigList


    def applyUpdateNodeConfig(self, sdk, config, update_func, readdata=None, rollback=False):
        delconfigList = []
        failurecfg = False
        data = config.getSdkConfig(readdata=readdata, rollback=rollback)
        (argumentList, kwargs) = self.get_sdk_func_key_values(data, update_func)
        if len(kwargs) > 0:
            r = update_func(*argumentList, **kwargs)
            # succes
            errorStr = r.json()['Error']
            if r.status_code not in (sdk.httpSuccessCodes) and ('exists' and 'Nothing to be updated') not in errorStr:
                sys.stdout.write("command update FAILED:\n%s %s\n" % (r.status_code, errorStr))
                failurecfg = True
            else:
                sys.stdout.write("update SUCCESS:   http status code: %s\n" % (r.status_code,))
                if r.json()['Error']:
                    sys.stdout.write("warning return code: %s\n" % (r.json()['Error']))

                # set configuration to applied state
                config.setPending(False)
                config.show()
                delconfigList.append(config)
            sys.stdout.write("sdk:%s(%s,%s)\n" % (update_func.__name__,
                                                  ",".join(["%s" % (x) for x in argumentList]),
                                                  ",".join(["%s=%s" % (x, y) for x, y in kwargs.iteritems()])))
        return (failurecfg, delconfigList)

    def do_showunapplied(self, argv):
        sys.stdout.write("Unapplied Config\n")
        for config in self.configList:
            if config.isValid():
                config.show()


    def do_clearunapplied(self, argv):
        sys.stdout.write("Clearing Unapplied Config\n")
        for config in self.configList:
            config.clear(all)

        self.configList = []


    '''
    TODO need to be able to run show at any time during config
    def do_compelte_show(self, text, line, begidx, endidx):
        mline = [self.objname] + [x for x in line.split(' ') if x != '']

        line = " ".join(mline[1:])
        self._cmd_complete_common(text, line, begidx, endidx)


    def do_show(self, argv):
        self.display_help(argv[1:])
    '''