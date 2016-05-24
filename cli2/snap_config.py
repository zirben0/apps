#!/usr/bin/python

import sys
from sets import Set
import cmdln
import json
import pprint
import inspect
from jsonref import JsonRef
from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine
from snap_leaf import LeafCmd
from cmdEntry import *

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
        #try:
            #import ipdb; ipdb.set_trace()
        cmdln.Cmdln.cmdloop(self)
        #except KeyboardInterrupt:
        #    self.intro = '\n'
        #    self.cmdloop()


    def validateSchemaAndModel(self):
        if self.model is None or self.schema is None:
            sys.exit(2)
        else:
            try:
                # lets validate the model against the json schema
                Draft4Validator(self.schema).validate(self.model)
            except Exception as e:
                print e
                return False
        return True

    def _cmd_complete_delete(self, text, line, begidx, endidx):
        #sys.stdout.write("\n%s line: %s text: %s %s\n" %('no ' + self.objname, line, text, not text))
        mline = [x for x in line.split(' ') if x != '']
        mline = mline[1:]
        #sys.stdout.write("\n%s mline %s\n" %('no ' + self.objname, mline))

        return self._cmd_complete_common(text, ' '.join(mline), begidx, endidx)

    def _cmd_do_delete(self, argv):

        self.cmdtype = 'delete'
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
                submodelList = self.getSubCommand(mline[i], submodel[schemaname]["commands"])
                #sys.stdout.write("config complete: submodelList = %s\n" %(submodelList))
                if submodelList:
                    subschemaList = self.getSubCommand(mline[i], subschema[schemaname]["properties"]["commands"]["properties"])
                    for submodel, subschema in zip(submodelList, subschemaList):
                        #sys.stdout.write("\ncomplete:  10 %s mline[i-1] %s mline[i] %s model %s\n" %(i, mline[i-i], mline[i], submodel))
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
        #import ipdb; ipdb.set_trace()
        if len(argv) != self.commandLen:
            self.cmdloop()

        # reset the command len
        self.commandLen = 0

        endprompt = self.baseprompt[-2:]
        # should be at config x
        schemaname = self.getSchemaCommandNameFromCliName(self.objname, self.model)
        submodelList = self.getSubCommand(argv[0], self.model[schemaname]["commands"])
        subschemaList = self.getSubCommand(argv[0], self.schema[schemaname]["properties"]["commands"]["properties"])
        schemaname = self.getSchemaCommandNameFromCliName(argv[0], submodelList[0])
        configprompt = self.getPrompt(submodelList[0][schemaname], subschemaList[0][schemaname])
        if self.cmdtype != 'delete':
            self.prompt = self.baseprompt[:-2] + '-' + configprompt + '-'

        value = None
        objname = schemaname
        for i in range(1, len(argv)-1):
            for submodel, subschema in zip(submodelList, subschemaList):
                schemaname = self.getSchemaCommandNameFromCliName(argv[i-1], submodel)

                submodelList = self.getSubCommand(argv[i], submodel[schemaname]["commands"])
                subschemaList = self.getSubCommand(argv[i], subschema[schemaname]["properties"]["commands"]["properties"])
                for submodel, subschema in zip(submodelList, subschemaList):
                    schemaname = self.getSchemaCommandNameFromCliName(argv[i], submodel)
                    configprompt = self.getPrompt(submodel[schemaname], subschema[schemaname])
                    objname = schemaname
                    if configprompt and self.cmdtype != 'delete':
                        self.prompt += configprompt + '-'
                        value = argv[-1]

        if value != None:
            self.prompt += value + endprompt
        elif self.cmdtype != 'delete':
            self.prompt = self.prompt[:-1] + endprompt
        self.stop = True
        prevcmd = self.currentcmd
        self.currentcmd = self.lastcmd
        # stop the command loop for config as we will be running a new cmd loop
        cmdln.Cmdln.stop = True

        self.teardownCommands()
        c = LeafCmd(objname, argv[-2], self.cmdtype, self, self.prompt, submodelList, subschemaList)
        if c.applybaseconfig(argv[-2]):
            c.cmdloop()
        self.setupCommands()
        if self.cmdtype == 'delete':
            self.cmdtype = 'config'

        self.prompt = self.baseprompt
        self.currentcmd = prevcmd
        self.cmdloop()

    def precmd(self, argv):
        mlineLength = len(argv) - (1 if 'no' in argv else 0)
        mline = [self.objname] + [x for x in argv if x != 'no']
        subschema = self.schema
        submodel = self.model
        if mlineLength > 0:
            self.commandLen = 0
            try:
                for i in range(1, len(mline)-1):
                    schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], submodel)
                    subschemaList = self.getSubCommand(mline[i], subschema[schemaname]["properties"]["commands"]["properties"])
                    submodelList = self.getSubCommand(mline[i], submodel[schemaname]["commands"])
                    for submodel, subschema in zip(submodelList, subschemaList):
                        valueexpected = self.isValueExpected(mline[i], submodel, subschema)
                        if valueexpected:
                            if mlineLength - i > 1:
                                sys.stdout.write("Invalid command entered, ignoring\n")
                                return ''

                            self.commandLen = mlineLength

            except Exception as e:
                sys.stdout.write("precmd: error %s" %(e,))
                pass

            cmd = argv[-1]
            if cmd in ('?', ) or \
                    (mlineLength < self.commandLen and cmd not in ("exit", "end", "help", "no")):
                self.display_help(argv)
                return ''

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
           'get' in func.__name__:
            for k in getKeys:
                if k in data:
                    argumentList.append(data[k])

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
                return config
        return None


    def show_state(self, all=False):

        configObj = self.getConfigObj()
        if configObj and configObj.configList:
            sys.stdout.write("Applying Show:\n")
            # tell the user what attributes are being applied
            for i in range(len(configObj.configList)):
                config = configObj.configList[-(i+1)]

                # get the sdk
                sdk = self.getSdkShow()

                funcObjName = config.name
                try:
                    if all:
                        printall_func = getattr(sdk, 'print' + funcObjName + 'States')
                        printall_func()
                    else:
                        # update all the arguments so that the values get set in the get_sdk_...
                        print_func = getattr(sdk, 'print' + funcObjName + 'State')
                        data = config.getSdkConfig()
                        (argumentList, kwargs) = self.get_sdk_func_key_values(data, print_func)
                        print_func(*argumentList)

                    # remove the configuration as it has been applied
                    config.clear(None, None, all=True)
                except Exception as e:
                    sys.stdout.write("FAILED TO GET OBJECT for show state: %s\n" %(e,))


    def do_apply(self, argv):
        if self.configList:

            sys.stdout.write("Applying Config:\n")
            # HACK need to make sure global objects are called before other objects
            globalconfigList = []
            otherconfig = []
            for config in self.configList:
                if "global" in config.name.lower():
                    globalconfigList.append(config)
                else:
                    otherconfig.append(config)

            for config in globalconfigList + otherconfig:
                if config.isValid():

                    # tell the user what attributes are being applied
                    #config.show()

                    # get the sdk
                    sdk = self.getSdk()

                    funcObjName = config.name

                    #lets see if the object exists, by doing a get first
                    get_func = getattr(sdk, 'get' + funcObjName)
                    update_func = getattr(sdk, 'update' + funcObjName)
                    create_func = getattr(sdk, 'create' + funcObjName)

                    try:
                        # update all the arguments
                        data = config.getSdkConfig()
                        (argumentList, kwargs) = self.get_sdk_func_key_values(data, get_func)

                        r = get_func(*argumentList)
                        if r.status_code in sdk.httpSuccessCodes:
                            # update
                            data = config.getSdkConfig()
                            (argumentList, kwargs) = self.get_sdk_func_key_values(data, update_func)
                            if len(kwargs) > 0:
                                r = update_func(*argumentList, **kwargs)
                                if r.status_code not in sdk.httpSuccessCodes:
                                    sys.stdout.write("command update FAILED:\n%s %s\n" %(r.status_code, r.json()['Error']))
                                else:
                                    sys.stdout.write("update SUCCESS:\n" )
                                    config.show()

                        elif r.status_code == 404:
                            # create
                            data = config.getSdkConfig()
                            (argumentList, kwargs) = self.get_sdk_func_key_values(data, create_func)
                            r = create_func(*argumentList)
                            if r.status_code not in sdk.httpSuccessCodes:
                                sys.stdout.write("command create FAILED:\n%s %s\n" %(r.status_code, r.json()['Error']))
                            else:
                                sys.stdout.write("create SUCCESS:\n" )
                                config.show()

                        else:
                            sys.stdout.write("Command Get FAILED\n%s %s\n" %(r.status_code, r.json()['Error']))

                        # remove the configuration as it has been applied
                        config.clear(None, None, all=True)
                    except Exception as e:
                        sys.stdout.write("FAILED TO GET OBJECT: %s\n" %(e,))

    def do_showunapplied(self, argv):
        sys.stdout.write("Unapplied Config\n")
        for config in self.configList:
            if config.isValid():
                config.show()


    def do_clearunapplied(self, argv):
        sys.stdout.write("Clearing Unapplied Config\n")
        for config in self.configList:
            config.clear(all)

    '''
    TODO need to be able to run show at any time during config
    def do_compelte_show(self, text, line, begidx, endidx):
        mline = [self.objname] + [x for x in line.split(' ') if x != '']

        line = " ".join(mline[1:])
        self._cmd_complete_common(text, line, begidx, endidx)


    def do_show(self, argv):
        self.display_help(argv[1:])
    '''