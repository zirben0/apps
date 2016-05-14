#!/usr/bin/python

import sys
from sets import Set
import cmdln
import json
import pprint
from jsonref import JsonRef

from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine
from snap_interface import InterfaceCmd
from snap_leaf import LeafCmd

pp = pprint.PrettyPrinter(indent=2)
class ConfigCmd(cmdln.Cmdln, CommonCmdLine):

    def __init__(self, parent, objname, prompt, model, schema):

        cmdln.Cmdln.__init__(self)
        self.objname = objname
        self.name = objname + ".json"
        self.parent = parent
        self.model = model
        self.schema = schema
        self.baseprompt = prompt
        self.prompt = self.baseprompt
        self.commandLen = 0

        # this loop will setup each of the cliname commands for this model level
        for subcmds, cmd in self.model[self.objname]["commands"].iteritems():
            # handle the links
            if 'subcmd' in subcmds:
                try:
                    for k,v in cmd.iteritems():
                        cmdname = self.getCliName(v)
                        setattr(self.__class__, "do_" + cmdname, self._cmd_common)
                        setattr(self.__class__, "complete_" + cmdname, self._cmd_complete_common)
                        sys.stdout.write("creating do_%s and complete_%s\n" %(cmdname, cmdname))
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED: %s" %(e,))
            else:
                # handle commands when are not links
                try:
                    setattr(self.__class__, "do_" + self.getCliName(self.model[self.objname][subcmds]), self._cmd_common)
                    sys.stdout.write("creating do_%s\n" %(self.getCliName(self.model[self.objname][subcmds])))
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED: %s" %(e,))

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
                Draft4Validator(self.model, self.schema)
            except Exception as e:
                print e
                return False
        return True

    def do_help(self, argv):
        if 'ethernet' in argv:
            sys.stdout.write("Command example: 'interface ethernet fpPort40' received '%s'\n\n" % (" ".join(argv)))
        elif 'vlan' in argv:
            sys.stdout.write("Command example: 'vlan 100' received %s\n\n" %(" ".join(argv)))

    def getchildrencmds(self, parentname, model, schema):

        if model:
            return [self.getCliName(cmdobj.values()[0]) for cmdobj in [obj for k, obj in model[parentname]["commands"].iteritems() if "subcmd" in k]]
        return []

    def _cmd_complete_common(self, text, line, begidx, endidx):
        #sys.stdout.write("\nline: %s text: %s %s\n" %(line, text, not text))
        # remove spacing/tab
        mline = [ x for x in line.split(' ') if x != '']
        mlineLength = len(mline)
        #sys.stdout.write("complete cmd: %s\ncommand %s objname %s\n\n" %(self.model, mline[0], self.objname))

        # lets get the child model and schema
        submodel = self.getSubCommand(mline[0], self.model[self.objname]["commands"])
        subschema = self.getSubCommand(mline[0], self.schema[self.objname]["properties"]["commands"]["properties"])
        #sys.stdout.write("2 submodel %s\n\n 2 subschema %s\n\n schema %s\n\n" %(submodel, subschema, self.schema[self.objname]))
        # get the sub commands for the child
        subcommands = self.getchildrencmds(mline[0], submodel, subschema)
        # check to see if this command is the last one before a value is expected
        valueexpected = self.isValueExpected(mline[0], subschema)

        #sys.stdout.write("submodel %s\n\n subschema %s\n\n valueexpected %s\n" %(submodel, subschema, valueexpected))
        if valueexpected:
            # set the total command length
            self.commandLen = mlineLength + 1
            #sys.stdout.write("returning value expected found subcommands %s\n" %(subcommands,))
            return subcommands

        # advance to next submodel and subschema
        for i in range(1, mlineLength):
            #sys.stdout.write("%s submodel %s\n\n i subschema %s\n\n subcommands %s mline %s\n\n" %(i, submodel, subschema, subcommands, mline[i-1]))
            if mline[i-1] in submodel:
                submodel = self.getSubCommand(mline[i], submodel[mline[i-1]]["commands"])
                if submodel:
                    #sys.stdout.write("\ncomplete:  10 %s mline[i-1] %s mline[i] %s subschema %s\n" %(i, mline[i-i], mline[i], subschema))
                    subschema = self.getSubCommand(mline[i], subschema[mline[i-1]]["properties"]["commands"]["properties"])
                    valueexpected = self.isValueExpected(mline[1], subschema)
                    if valueexpected:
                        self.commandLen = len(mline) + 1
                        return []
                    else:
                        subcommands = self.getchildrencmds(mline[i], submodel, subschema)

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
            self.cmdloop()
        value = argv[-1]
        # reset the command len
        self.commandLen = 0
        endprompt = self.baseprompt[-2:]

        submodel = self.getSubCommand(argv[0], self.model[self.objname]["commands"])
        subschema = self.getSubCommand(argv[0], self.schema[self.objname]["properties"]["commands"]["properties"])

        configprompt = self.getPrompt(submodel[argv[0]], subschema[argv[0]])
        self.prompt = self.baseprompt[:-2] + '-' + configprompt + '-'

        for i in range(1, len(argv)-1):

            submodel = self.getSubCommand(argv[i], submodel[argv[i-1]]["commands"])
            subschema = self.getSubCommand(argv[i], subschema[argv[i-1]]["properties"]["commands"]["properties"])

            configprompt = self.getPrompt(submodel[argv[i]], subschema[argv[i]])
            self.prompt += configprompt + '-'

        self.prompt += value + endprompt
        self.stop = True
        c = LeafCmd(argv[-2], self, self.prompt, submodel, subschema)
        c.cmdloop()
        self.prompt = self.baseprompt

        self.cmdloop()

    def precmd(self, argv):
        mlineLength = len(argv)
        mline = argv

        try:
            # lets walk through the commands inputed so far to determine the command len
            subschema = self.getSubCommand(mline[0], self.schema[self.objname]["properties"]["commands"]["properties"])
            valueexpected = self.isValueExpected(mline[0], subschema)
            if valueexpected:
                self.commandLen = mlineLength
        except Exception:
            pass

        cmd = argv[-1]
        if cmd in ('?', ) or \
                (mlineLength < self.commandLen and cmd not in ("exit", "end", "help")):
            self.do_help(argv)
            return ''

        return argv

    def do_router(self):
        pass

    def do_ip(self):
        pass

