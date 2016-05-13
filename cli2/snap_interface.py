#!/usr/bin/python

import sys
import cmdln
import json
from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine

class InterfaceCmd(cmdln.Cmdln, CommonCmdLine):

    # schema and model name
    name = "interface.json"
    def __init__(self, parent, prompt, model, schema):

        cmdln.Cmdln.__init__(self)
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

    def setModel(self):

        with open(self.modelpath, "r") as json_model_data:
            self.model = json.load(json_model_data)


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

    cmdln.alias("eth", "ether")
    def do_ethernet(self, arg):
        import ipdb; ipdb.set_trace()

        pend = self.baseprompt[-2:]
        self.prompt = self.baseprompt[:-2] + self.model["interface"]["prompt"] + pend
        self.cmdloop()
        pass

    def do_router(self):
        pass

    def do_ip(self):
        pass

    def precmd(self, argv):
        import ipdb; ipdb.set_trace()
        print argv
        if 'ethernet' in argv:
            if 'help' or '?' in argv:
                sys.stdout.write("cmd" + self.lastcmd)


