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
    def __init__(self, objname, parent, prompt, model, schema):

        cmdln.Cmdln.__init__(self)

        self.objname = objname
        self.name = objname + ".json"
        self.parent = parent
        self.model = model
        self.schema = schema
        self.baseprompt = prompt
        self.prompt = self.baseprompt

        allCmdsDict = self.getCliCmdAttr(None, self.model[self.objname]["commands"])
        # update the keys with appropriate values from parent command
        allCmdsDict.update(self.getUniqueKeyFromCliNameList())

        self.config = CmdEntry(self.getObjName(), allCmdsDict)
        #sys.stdout.write("LeafCmd: %s" % self.model)

        self.setupCommands()

    def getCliNameToObjName(self):
        for k, v in self.model[self.objname]["commands"].iteritems():
            print k,v


    def getObjName(self,):
        cmd = 'objname'
        return self.getSubCommand(cmd, self.schema[self.objname]["properties"]["commands"]["properties"])[cmd]['default']

    def getUniqueKeyFromCliNameList(self,):
        keyDict = {}
        for i, c in enumerate(self.parent.lastcmd):
            subcmd = self.getCliCmdAttr(c, self.model[self.objname]["commands"])
            if subcmd:
                # lets set the key value
                subcmd[c]['value'] = self.parent.lastcmd[i+1]
                keyDict.update(subcmd)
        return keyDict

    def getCliCmdAttr(self, key, commands):
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

        #self.cmdloop()




