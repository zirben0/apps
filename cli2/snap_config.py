#!/usr/bin/python

import sys
from sets import Set
import cmdln
import json
from pprint import pprint
from jsonref import JsonRef

from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine
from snap_interface import InterfaceCmd
from snap_leaf import LeafCmd

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

        # this loop will setup each of the cliname commands for this model level
        for subcmds, cmd in self.model[self.objname]["commands"].iteritems():
            # handle the links
            if 'subcmd' in subcmds:
                try:
                    for k,v in cmd.iteritems():
                        cmdname = self.getCliName(v)
                        setattr(self.__class__, "do_" + cmdname, self.__getattribute__("_cmd_%s" %(k,)))
                        setattr(self.__class__, "complete_" + cmdname, self.__getattribute__("_cmd_complete_%s" %(k,)))
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED: %s" %(e,))
            else:
                # handle commands when are not links
                try:
                    setattr(self.__class__, "do_" + self.getCliName(self.model[self.objname][subcmds]), self.__getattribute__("_cmd_%s" %(subcmds,)))
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED: %s" %(e,))

    def cmdloop(self, intro=None):
        try:
            cmdln.Cmdln.cmdloop(self)
        except KeyboardInterrupt:
            self.intro = '\n'
            self.cmdloop()


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

    def getchildrencmds(self, parentname, model, schema):

        return [self.getCliName(cmdobj.values()[0]) for cmdobj in [obj for k, obj in model[parentname]["commands"].iteritems() if "subcmd" in k]]

    def _cmd_complete_interface(self, text, line, begidx, endidx):
        #sys.stdout.write("line: %s\n text: %s %s %s" %(line, text, not text, len(text)))
        # remove spacing/tab
        mline = [ x for x in line.split(' ') if x != '']

        #functionNameAsString = sys._getframe().f_code.co_name
        #name = functionNameAsString.split("_")[-1]

        #sys.stdout.write("complete interface: %s\ncommand %s objname %s\n\n" %(self.model, mline[0], self.objname))

        # lets get the children commands
        submodel = self.getSubCommand(mline[0], self.model[self.objname]["commands"])
        subschema = self.getSubCommand(mline[0], self.schema[self.objname]["properties"]["commands"]["properties"])
        #sys.stdout.write("2 submodel %s\n\n 2 subschema %s\n\n" %(submodel, subschema))
        subcommands = self.getchildrencmds(mline[0], submodel, subschema)
        # todo should look next command so that this is not 'sort of hard coded'
        # todo should to a getall at this point to get all of the interface types once a type is found
        #sys.stdout.write("3: subcommands: %s\n\n" %(subcommands,))

        # lets remove any duplicates
        returncommands = Set(subcommands).difference(mline)

        if len(text) == 0 and len(returncommand) == len(subcommands):
            return returncommands
        elif len(text) == 0:
            # todo get all interfaces
            pass
        # lets only get commands which are a partial of what was entered
        returncommands = [k for k in returncommands if k.startswith(text)]
        return returncommands



    def _cmd_interface(self, argv):

        if len(argv) < 3:
            self.cmdloop()

        cmd = argv[0]
        subcmd = argv[1]
        value = argv[2]

        endprompt = self.baseprompt[-2:]
        submodel = self.getSubCommand(cmd, self.model[self.objname]["commands"])
        subschema = self.getSubCommand(cmd, self.schema[self.objname]["properties"]["commands"]["properties"])
        subsubmodel = self.getSubCommand(subcmd, submodel[cmd]["commands"])
        subsubschema = self.getSubCommand(subcmd, subschema[cmd]["properties"]["commands"]["properties"])

        configprompt = self.getPrompt(submodel[cmd], subschema[cmd])
        self.prompt = self.baseprompt[:-2] + configprompt + '-' + value + endprompt
        self.stop = True
        c = LeafCmd(subcmd, self, self.prompt, subsubmodel, subsubschema)
        c.cmdloop()
        self.prompt = self.baseprompt

        self.cmdloop()

    def precmd(self, argv):
        length =  len(argv)
        if length > 1:
            cmd = argv[1]
            if cmd in ('?', ) or \
                    (length < 3 and cmd not in ("exit", "end", "help")):
                self.do_help(argv)
                return ''
        return argv

    def do_router(self):
        pass

    def do_ip(self):
        pass

