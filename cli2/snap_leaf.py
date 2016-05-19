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
    def __init__(self, objname, cmdtype, parent, prompt, modelList, schemaList):

        cmdln.Cmdln.__init__(self)

        self.objname = objname
        self.name = objname + ".json"
        self.parent = parent
        self.modelList = modelList
        self.schemaList = schemaList
        self.baseprompt = prompt
        self.prompt = self.baseprompt
        self.cmdtype = cmdtype
        self.currentcmd = []
        self.configList = []

        for model, schema in zip(self.modelList, self.schemaList):

            # lets get all commands and subcommands for a given config operation
            allCmdsList = self.getCliCmdAttrs(None, self.objname, None, model[self.objname]["commands"], schema[self.objname]["properties"]["commands"]["properties"])
            objDict = {}

            for cmds in allCmdsList:
                for k, v in cmds.iteritems():
                    if v['objname'] not in objDict:
                        objDict[v['objname']] = {}

                    objDict[v['objname']].update({k:v})

            for k, v in objDict.iteritems():
                self.configList.append(CmdEntry(k, objDict[k]))

            #sys.stdout.write("LeafCmd: %s" % self.model)

        # update the parents attribute info to the subcommands
        if self.objname != self.parent.lastcmd[-1]:
            for cmdEntry in self.configList:
                basekey = self.parent.lastcmd[-2]
                basevalue = self.parent.lastcmd[-1]
                cmdEntry.set(basekey, basevalue)

        self.setupCommands()


    def getObjName(self, schema):
        cmd = 'objname'
        return self.getSubCommand(cmd, schema[self.objname]["properties"]["commands"]["properties"])[0][cmd]['default']

    def getUniqueKeyFromCliNameList(self, model, cmd):
        keyDict = {}
        for i, c in enumerate(cmd):
            subcmd = self.getCliCmdAttrs(c, model[self.objname]["commands"])
            if subcmd and c in subcmd:
                # lets set the key value
                subcmd[c]['value'] = self.parent.lastcmd[i+1] if self.cmdtype == 'config' else None
                keyDict.update(subcmd)
        return keyDict

    def getCliCmdAttrs(self, key, objname, subcmd, model, schema):
        cmdList = []
        cmdDict = {}
        tmpobjname = objname
        for k, v in model.iteritems():
            tmpschema = schema[k]
            if k == key:
                return v
            try:
                if 'objname' in tmpschema:
                    tmpobjname = tmpschema['objname']['default']
            except Exception:
                pass
            # looking for subcommand
            if "subcmd" in k and "commands" in v and type(v["commands"]) in (dict, jsonref.JsonRef):
                cmds = self.getCliCmdAttrs(key, tmpobjname, subcmd, v["commands"], tmpschema["commands"]["properties"])
                cmdList += cmds
            # looking for subsubcommand
            elif "subcmd" in k and type(v) in (dict, jsonref.JsonRef):
                for kk, vv in v.iteritems():
                    subtmpschema = tmpschema[kk]['properties']
                    try:
                        if 'objname' in subtmpschema:
                            tmpobjname = subtmpschema['objname']['default']
                    except Exception:
                        pass

                    tmpsubcmd = None
                    if 'cliname' in vv:
                        if subcmd is None:
                            tmpsubcmd = vv['cliname']
                        else:
                            tmpsubcmd = subcmd + vv['cliname']

                    if "commands" in vv:
                        cmds = self.getCliCmdAttrs(key, tmpobjname, tmpsubcmd, vv["commands"], subtmpschema["commands"]["properties"])
                        cmdList += cmds

            else:
                cmdDict.update({v['cliname'] : {'key': k,
                                                'subcommand' : subcmd,
                                                'objname' : objname,
                                                'value': None}})
        if cmdDict:
            cmdList.append(cmdDict)

        return cmdList

    def setupCommands(self):
        # this loop will setup each of the cliname commands for this model level
        # cmdln/cmd expects that all commands have a function associated with it
        # in the format of 'do_<command>'
        # TODO need to add support for when the cli mode does not supply the cliname
        #      in this case need to get the default from the schema model
        for model, schema in zip(self.modelList, self.schemaList):
            for subcmds, cmd in model[self.objname]["commands"].iteritems():
                # handle the links
                if 'subcmd' in subcmds:
                    try:
                        if "commands" in cmd:
                            for k,v in cmd["commands"].iteritems():
                                cmdname = self.getCliName(v)
                                # Note needed for show
                                #if cmdname != self.objname:
                                setattr(self.__class__, "do_" + cmdname, SetAttrFunc(self._cmd_default))
                                #setattr(self.__class__, "complete_" + cmdname, self.__getattribute__("_cmd_complete_%s" %(k,)))
                        else:
                            # another sub command list
                            for k, v in cmd.iteritems():
                                cmdname = self.getCliName(v)
                                # Note needed for show
                                #if cmdname != self.objname:
                                setattr(self.__class__, "do_" + cmdname, SetAttrFunc(self._cmd_default))
                                setattr(self.__class__, "complete_" + cmdname, self._cmd_complete)

                    except Exception as e:
                            sys.stdout.write("EXCEPTION RAISED: %s" %(e,))
                else:
                    # handle commands when are not links
                    try:
                        setattr(self.__class__, "do_" + self.getCliName(model[self.objname][subcmds]["commands"]), SetAttrFunc(self._cmd_default))
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
        elif len(argv) == 2:
            # key value supplied
            key = None
            subkey = argv[0]
            value = argv[1]

            for config in self.configList:
                if subkey in config.keysDict.keys():
                    # store the attribute into the config
                    config.set(subkey, value)
        else:
            # key + subkey + value supplied
            key = argv[0]
            subkey = argv[1]
            value = argv[2]
            for config in self.configList:
                if subkey in config.keysDict.keys():
                    config.set(subkey, value)


    def getchildrencmds(self, parentname, model, schema):
        attrlist = []
        if model:
            for cmdobj in [obj for k, obj in model[parentname]["commands"].iteritems() if "subcmd" in k]:
                for v in cmdobj["commands"].values():
                    if v['cliname'] != self.objname:
                        attrlist.append(v['cliname'])
        return attrlist

    # this complete is meant for sub ethernet commands
    # for example:
    # >ip address 10.1.1.1
    def _cmd_complete(self, text, line, begidx, endidx):
        #sys.stdout.write("\nline: %s text: %s %s\n" %(line, text, not text))
        # remove spacing/tab
        mline = [self.objname] + [x for x in line.split(' ') if x != '']
        mlineLength = len(mline)

        subcommands = []
        for i in range(1, mlineLength):
            for model, schema in zip(self.modelList, self.schemaList):
                #sys.stdout.write("model %s\n schema %s\n mline[%s] %s\n" %(model, schema, i, mline[i]))
                submodelList = self.getSubCommand(mline[i], model[mline[i-1]]["commands"])
                #sys.stdout.write("submoduleList %s\n" %(submodelList,))
                if submodelList:
                    subschemaList = self.getSubCommand(mline[i], schema[mline[i-1]]["properties"]["commands"]["properties"])
                    #sys.stdout.write("subschemaList %s\n" %(subschemaList,))
                    for submodel, subschema in zip(submodelList, subschemaList):
                        #sys.stdout.write("submodel %s\n subschema %s\n mline %s" %(submodel, subschema, mline[i]))
                        subcommands += self.getchildrencmds(mline[i], submodel, subschema)
                        #sys.stdout.write("subcommands %s" %(subcommands,))

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


    def get_sdk_func_key_values(self, config, kwargs, func):
            argspec = inspect.getargspec(func)
            getKeys = argspec.args[1:]
            lengthkwargs = len(argspec.defaults) if argspec.defaults is not None else 0
            if lengthkwargs > 0:
                getKeys = argspec.args[:-len(argspec.defaults)]

            # lets setup the argument list
            argumentList = []
            for k in getKeys:
                if k in kwargs:
                    del kwargs[k]
                for v in config.keysDict.values():
                    if v['key'] == k:
                        argumentList.append(v['value'])
            return argumentList


    def show_state(self, all=False):

        if self.configList:
            sys.stdout.write("Applying Show:\n")
            # tell the user what attributes are being applied
            for i in range(len(self.configList)):
                config = self.configList[-(i+1)]
                #config.show()

                # get the sdk
                sdk = self.getSdkShow()

                funcObjName = config.name
                try:
                    #lets see if the object exists, by doing a get first
                    printall_func = getattr(sdk, 'print' + funcObjName + 'States')
                    print_func = getattr(sdk, 'print' + funcObjName + 'State')

                    # update all the arguments so that the values get set in the get_sdk_...
                    kwargs = config.getSdkAll()
                    argumentList = self.get_sdk_func_key_values(config, kwargs, print_func)

                    if all:
                        printall_func()
                    else:
                        print_func(*argumentList)

                    # remove the configuration as it has been applied
                    config.clear(None, None, all=True)
                except Exception as e:
                    sys.stdout.write("FAILED TO GET OBJECT for show state: %s\n" %(e,))


    def do_apply(self, argv):

        if self.configList:
            sys.stdout.write("Applying Config:\n")
            for config in self.configList:
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
                    kwargs = config.getSdkAll()
                    argumentList = self.get_sdk_func_key_values(config, kwargs, get_func)

                    r = get_func(*argumentList)
                    if r.status_code in sdk.httpSuccessCodes:
                        # update
                        argumentList = self.get_sdk_func_key_values(config, kwargs, update_func)
                        if len(kwargs) > 0:
                            r = update_func(*argumentList, **kwargs)
                            if r.status_code not in sdk.httpSuccessCodes:
                                sys.stdout.write("command update FAILED:\n%s %s" %(r.status_code, r.json()['Error']))

                    elif r.status_code == 404:
                        # create
                        argumentList = self.get_sdk_func_key_values(config, kwargs, create_func)
                        r = create_func(*argumentList, **kwargs)
                        if r.status_code not in sdk.httpSuccessCodes:
                            sys.stdout.write("command create FAILED:\n%s %s" %(r.status_code, r.json()['Error']))

                    else:
                        sys.stdout.write("Command Get FAILED\n%s %s" %(r.status_code, r.json()['Error']))

                    # remove the configuration as it has been applied
                    config.clear(None, None, all=True)
                except Exception as e:
                    sys.stdout.write("FAILED TO GET OBJECT: %s" %(e,))

    def do_showunapplied(self, argv):
        sys.stdout.write("Unapplied Config")
        for config in self.configList:
            config.show()


    def do_clearunapplied(self, argv):
        sys.stdout.write("Clearing Unapplied Config")
        for config in self.configList:
            config.clear()
