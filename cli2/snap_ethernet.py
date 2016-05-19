#!/usr/bin/python

import sys
import cmdln
import json
from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine

class EthernetCmd(cmdln.Cmdln, CommonCmdLine):

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

        # this loop will setup each of the cliname commands for this model level
        for subcmds, cmd in self.model[self.objname]["commands"].iteritems():
            # handle the links
            if 'subcmd' in subcmds:
                try:
                    for k,v in cmd.iteritems():
                        cmdname = self.getCliName(v)
                        setattr(self.__class__, "do_" + cmdname, self._cmd_default)
                        #setattr(self.__class__, "complete_" + cmdname, self.__getattribute__("_cmd_complete_%s" %(k,)))
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED: %s" %(e,))
            else:
                # handle commands when are not links
                try:
                    setattr(self.__class__, "do_" + self.getCliName(self.model[self.objname][subcmds]), self._cmd_default)
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED: %s" %(e,))



        sys.stdout.write("EthernetCmd: %s" % self.model)

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
        self.configDict.update({key:value})

        self.cmdloop()




