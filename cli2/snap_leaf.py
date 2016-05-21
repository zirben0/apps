#!/usr/bin/python

import sys
import cmdln
import json
import jsonref

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
    def __init__(self, objname, cliname, cmdtype, parent, prompt, modelList, schemaList):

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

        configObj = self.getConfigObj()
        for model, schema in zip(self.modelList, self.schemaList):

            # lets get all commands and subcommands for a given config operation
            allCmdsList = self.getCliCmdAttrs(None, self.objname, None, model[self.objname]["commands"], schema[self.objname]["properties"]["commands"]["properties"])
            objDict = {}

            for cmds in allCmdsList:
                for k, v in cmds.iteritems():
                    if v['objname'] not in objDict:
                        objDict[v['objname']] = {}

                    objDict[v['objname']].update({k:v})

            if configObj:
                for k, v in objDict.iteritems():
                    config = CmdEntry(k, objDict[k])
                    if cliname != self.parent.lastcmd[-1]:
                        basekey = self.parent.lastcmd[-2]
                        basevalue = self.parent.lastcmd[-1]
                        config.set(basekey, basevalue)
                    configObj.configList.append(config)

            #sys.stdout.write("LeafCmd: %s" % self.model)

        '''
        # update the parents attribute info to the subcommands
        if cliname != self.parent.lastcmd[-1]:
            if configObj:
                for config in configObj.configList:
                    if config.name == self.objname:
                        basekey = self.parent.lastcmd[-2]
                        basevalue = self.parent.lastcmd[-1]
                        config.set(basekey, basevalue)
        '''
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
                                if '-' in cmdname:
                                    sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                                    self.do_exit([])
                                    cmdname = cmdname.replace('-', '_')
                                setattr(self.__class__, "do_" + cmdname, SetAttrFunc(self._cmd_default))
                                #setattr(self.__class__, "complete_" + cmdname, self.__getattribute__("_cmd_complete_%s" %(k,)))
                        else:
                            # another sub command list
                            for k, v in cmd.iteritems():
                                cmdname = self.getCliName(v)
                                if '-' in cmdname:
                                    sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                                    self.do_exit([])
                                    cmdname = cmdname.replace('-', '_')
                                # Note needed for show
                                #if cmdname != self.objname:
                                setattr(self.__class__, "do_" + cmdname, SetAttrFunc(self._cmd_default))
                                setattr(self.__class__, "complete_" + cmdname, self._cmd_complete)

                    except Exception as e:
                            sys.stdout.write("EXCEPTION RAISED: %s" %(e,))
                else:
                    # handle commands when are not links
                    try:
                        cmdname = self.getCliName(model[self.objname][subcmds]["commands"])
                        if '-' in cmdname:
                            sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                            self.do_exit([])
                            cmdname = cmdname.replace('-', '_')
                        setattr(self.__class__, "do_" + cmdname, SetAttrFunc(self._cmd_default))
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

            configObj = self.getConfigObj()
            if configObj:
                for config in configObj.configList:
                    if subkey in config.keysDict.keys():
                        # store the attribute into the config
                        config.set(subkey, value)
        else:
            # key + subkey + value supplied
            key = argv[0]
            subkey = argv[1]
            value = argv[2]
            configObj = self.getConfigObj()
            if configObj:
                for config in configObj.configList:
                    if subkey in config.keysDict.keys():
                        config.set(subkey, value)


    def getchildrencmds(self, parentname, model, schema):
        attrlist = []
        if model:
            schemaname = self.getSchemaCommandNameFromCliName(parentname, model)
            for cmdobj in [obj for k, obj in model[schemaname]["commands"].iteritems() if "subcmd" in k]:
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
                schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], model)
                submodelList = self.getSubCommand(mline[i], model[schemaname]["commands"])
                #sys.stdout.write("submoduleList %s\n" %(submodelList,))
                if submodelList:
                    subschemaList = self.getSubCommand(mline[i], schema[schemaname]["properties"]["commands"]["properties"])
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

    def show_state(self, all=False):
        configObj = self.getConfigObj()
        if configObj:
            configObj.show_state(all)

    def display_help(self, argv):
        mline = [self.objname] + argv
        mlineLength = len(mline)
        #sys.stdout.write("complete cmd: %s\ncommand %s objname %s\n\n" %(self.model, mline[0], self.objname))

        #submodel = self.model
        #subschema = self.schema
        subcommands = []
        for model, schema in zip(self.modelList, self.schemaList):
            subcommands = self.getchildrenhelpcmds(mline[0], model, schema)

        for i in range(1, mlineLength-1):
            for model, schema in zip(self.modelList, self.schemaList):
                schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], model)
                #sys.stdout.write("model %s\n schema %s\n mline[%s] %s\n" %(model, schema, i, mline[i]))
                submodelList = self.getSubCommand(mline[i], model[schemaname]["commands"])
                if submodelList:
                    subschemaList = self.getSubCommand(mline[i], schema[schemaname]["properties"]["commands"]["properties"])
                    for submodel, subschema in zip(submodelList, subschemaList):
                        #sys.stdout.write("submodel %s\n subschema %s\n mline %s" %(submodel, subschema, mline[i]))
                        subcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema)

        self.printCommands(mline, subcommands)

    def do_help(self, argv):
        self.display_help(argv)

    def precmd(self, argv):
        return CommonCmdLine.precmd(self, argv)
