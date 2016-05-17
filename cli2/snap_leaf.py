#!/usr/bin/python

import sys
import cmdln
import json
import jsonref
import inspect
from sets import Set
from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine
from cmdEntry import CmdEntry

# used to
class SetAttrFunc(object):
    def __init__(self, func):
        self.name = func.__name__
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

# leaf means we are at a point of configuration
class LeafCmd(cmdln.Cmdln, CommonCmdLine):

    # schema and model name
    def __init__(self, objname, cmdtype, parent, prompt, model, schema):

        cmdln.Cmdln.__init__(self)

        self.objname = objname
        self.name = objname + ".json"
        self.parent = parent
        self.model = model
        self.schema = schema
        self.baseprompt = prompt
        self.prompt = self.baseprompt
        self.currentcmd = []
        self.cmdtype = cmdtype

        allCmdsDict = self.getCliCmdAttrs(None, self.model[self.objname]["commands"])
        # update the keys with appropriate values from parent command
        allCmdsDict.update(self.getUniqueKeyFromCliNameList(self.parent.lastcmd))

        self.config = CmdEntry(self.getObjName(), allCmdsDict)
        #sys.stdout.write("LeafCmd: %s" % self.model)

        self.setupCommands()

    def getCliNameToObjName(self):
        for k, v in self.model[self.objname]["commands"].iteritems():
            print k, v


    def getObjName(self,):
        cmd = 'objname'
        return self.getSubCommand(cmd, self.schema[self.objname]["properties"]["commands"]["properties"])[cmd]['default']

    def getUniqueKeyFromCliNameList(self, cmd):
        keyDict = {}
        for i, c in enumerate(cmd):
            subcmd = self.getCliCmdAttrs(c, self.model[self.objname]["commands"])
            if subcmd:
                # lets set the key value
                subcmd[c]['value'] = self.parent.lastcmd[i+1] if self.cmdtype == 'config' else None
                keyDict.update(subcmd)
        return keyDict

    def getCliCmdAttrs(self, key, commands):
        cmdDict = {}
        for k, v in commands.iteritems():
            if k == key:
                return v

            # looking for subcommand
            if "commands" in v and type(v["commands"]) in (dict, jsonref.JsonRef):
                for attrk, attrv in v["commands"].iteritems():
                    if attrv['cliname'] == key or key is None:
                        cmdDict.update({attrv['cliname']: {'key': attrk,
                                                   'value': None}})
        return cmdDict

    def setupCommands(self):
        # this loop will setup each of the cliname commands for this model level
        # cmdln/cmd expects that all commands have a function associated with it
        # in the format of 'do_<command>'
        # TODO need to add support for when the cli mode does not supply the cliname
        #      in this case need to get the default from the schema model
        for subcmds, cmd in self.model[self.objname]["commands"].iteritems():
            # handle the links
            if 'subcmd' in subcmds:
                try:
                    for k,v in cmd["commands"].iteritems():
                        cmdname = self.getCliName(v)
                        setattr(self.__class__, "do_" + cmdname, SetAttrFunc(self._cmd_default))
                        #setattr(self.__class__, "complete_" + cmdname, self.__getattribute__("_cmd_complete_%s" %(k,)))
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED: %s" %(e,))
            else:
                # handle commands when are not links
                try:
                    setattr(self.__class__, "do_" + self.getCliName(self.model[self.objname][subcmds]["commands"]), SetAttrFunc(self._cmd_default))
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED: %s" %(e,))

    def cmdloop(self, intro=None):
        try:
            cmdln.Cmdln.cmdloop(self)
        except KeyboardInterrupt:
            self.intro = '\n'
            self.cmdloop()


    def _cmd_default(self, argv):

        if len(argv) < 2:
            return

        key = argv[0]
        value = argv[1]

        # store the attribute into the config
        self.config.set(key, value)

    def show_state(self, all=False):

        def get_sdk_func_key_values(func):
            argspec = inspect.getargspec(func)
            getKeys = argspec.args[1:]
            lengthkwargs = len(argspec.defaults) if argspec.defaults is not None else 0
            if lengthkwargs > 0:
                getKeys = argspec.args[:-len(argspec.defaults)]

            # lets setup the argument list
            argumentList = []
            for k in getKeys:
                for v in self.config.keysDict.values():
                    if v['key'] == k:
                        argumentList.append(v['value'])
            return argumentList

        if self.config:
            sys.stdout.write("Applying Show:\n")
            # tell the user what attributes are being applied
            self.config.show()

            # get the sdk
            sdk = self.getSdkShow()

            funcObjName = self.config.name

            #lets see if the object exists, by doing a get first
            printall_func = getattr(sdk, 'print' + funcObjName + 'States')
            print_func = getattr(sdk, 'print' + funcObjName + 'State')

            # update all the arguments so that the values get set in the get_sdk_...
            self.config.getSdkAll()
            argumentList = get_sdk_func_key_values(print_func)
            try:
                if all:
                    printall_func()
                else:
                    print_func(*argumentList)
            except Exception as e:
                sys.stdout.write("FAILED TO GET OBJECT: %s")

            # remove the configuration as it has been applied
            self.config.clear(None, None, all=True)

    def do_apply(self, argv):

        def get_sdk_func_key_values(func):
            argspec = inspect.getargspec(func)
            getKeys = argspec.args[1:]
            lengthkwargs = len(argspec.defaults) if argspec.defaults is not None else 0
            if lengthkwargs > 0:
                getKeys = argspec.args[:-len(argspec.defaults)]

            # lets setup the argument list
            argumentList = []
            for k in getKeys:
                for v in self.config.keysDict.values():
                    if v['key'] == k:
                        argumentList.append(v['value'])
            return argumentList

        if self.config:
            sys.stdout.write("Applying Config:\n")
            # tell the user what attributes are being applied
            self.config.show()

            # get the sdk
            sdk = self.getSdk()

            funcObjName = self.config.name

            #lets see if the object exists, by doing a get first
            get_func = getattr(sdk, 'get' + funcObjName)
            update_func = getattr(sdk, 'update' + funcObjName)
            create_func = getattr(sdk, 'create' + funcObjName)

            # update all the arguments
            kwargs = self.config.getSdkAll()
            argumentList = get_sdk_func_key_values(get_func)
            try:
                r = get_func(*argumentList)
                if r.status_code in sdk.httpSuccessCodes:
                    # update
                    r = update_func(*argumentList, **kwargs)
                    if r.status_code not in sdk.httpSuccessCodes:
                        sys.stdout.write("command failed %s %s" %(r.status_code, r.json()))
                elif r.status_code == 404:
                    # create
                    create_func(*argumentList, **kwargs)
            except Exception as e:
                sys.stdout.write("FAILED TO GET OBJECT: %s")

            # remove the configuration as it has been applied
            self.config.clear(None, None, all=True)

    def do_showunapplied(self, argv):
        sys.stdout.write("Unapplied Config")
        self.config.show()


    def do_clearunapplied(self, argv):
        sys.stdout.write("Clearing Unapplied Config")

        self.configDict = {}
