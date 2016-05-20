#!/usr/bin/python
import copy
import jsonref
import sys
from jsonschema import Draft4Validator
import pprint
import requests



USING_READLINE = True
try:
    # For platforms without readline support go visit ...
    # http://pypi.python.org/pypi/readline/
    import readline
    import rlcompleter
    if 'libedit' in readline.__doc__:
    	readline.parse_and_bind("bind ^I rl_complete")
    else:
    	readline.parse_and_bind("tab: complete")
except:   se

pp = pprint.PrettyPrinter(indent=2)

class CommonCmdLine(object):

    configDict = {}
    def __init__(self, parent, switch_ip, schema_path, model_path, layer):
        if not USING_READLINE:
            self.completekey = None
        self.config = None
        self.parent = parent
        self.switch_ip = switch_ip
        self.switch_name = None
        self.model = None
        self.modelpath = model_path + layer
        self.schema = None
        self.schemapath = schema_path + layer
        self.baseprompt = "DEFAULT"
        self.setSchema()
        self.setModel()
        self.currentcmd = []
        valid = self.validateSchemaAndModel()

        if not valid:
            sys.stdout.write("schema and model mismatch")
            sys.exit(0)

    def getSdk(self):
        sdk = True
        parent = self.parent
        child = self

        def getparent(child):
            return child.parent

        # to prevent looping forever going to not accept
        # a tree larger than 10 levels
        root = None
        while root is None:
            # root node has no parent
            # and it holds the sdk
            if parent is None:
                root = child.sdk
            else:
                child = parent

            if not root:
                parent = getparent(child)
        return root

    def getSdkShow(self):
        parent = self.parent
        child = self

        def getparent(child):
            return child.parent

        # to prevent looping forever going to not accept
        # a tree larger than 10 levels
        root = None
        while root is None:
            # root node has no parent
            # and it holds the sdk
            if parent is None:
                root = child.sdkshow
            else:
                child = parent

            if not root:
                parent = getparent(child)
        return root


    def getSubCommand(self, key, commands):

        subList = []
        for k, v in commands.iteritems():
            if k == key:
                #sys.stdout.write("RETURN 1 %s\n\n"% (v))
                subList.append(v)

            # looking for subcommand
            if type(v) in (dict, jsonref.JsonRef) and ((key in v) or key in ('?', 'help')):
                #sys.stdout.write("RETURN 2 %s\n\n"% (v.keys()))
                subList.append(v)
        return subList

    def getchildrencmds(self, parentname, model, schema):
        # working model
        #if model:
        #    return [self.getCliName(cmdobj.values()[0]) for cmdobj in [obj for k, obj in model[parentname]["commands"].iteritems() if "subcmd" in k]]
        cliNameList = []
        if schema:
            for k, schemaobj in schema[parentname]["properties"]["commands"]["properties"].iteritems():
                if "subcmd" in k:
                    cliname = None
                    modelobj = model[parentname]["commands"][k] if k in model[parentname]["commands"] else None
                    if modelobj:
                        for kk, vv in modelobj.iteritems():
                            cliname = self.getCliName(vv)
                    # did not find the name in the model lets get from schema
                    if cliname is None:
                        for kk, vv in schemaobj.iteritems():
                            cliname = self.getCliName(vv)

                    cliNameList.append(cliname)
        return cliNameList

    def getchildrenhelpcmds(self, parentname, model, schema):
        cliHelpList = []
        if schema:
            for k, schemaobj in schema[parentname]["properties"]["commands"]["properties"].iteritems():
                if "subcmd" in k:
                    cliname = None
                    modelobj = model[parentname]["commands"][k] if k in model[parentname]["commands"] else None
                    x = []
                    if modelobj:
                        for kk, vv in modelobj.iteritems():
                            # leaf node
                            if kk == "commands":
                                for kkk, vvv in vv.iteritems():
                                    x.append([kkk, self.getCliName(vvv), self.getCliHelp(vvv)])
                            else:
                                x.append([kk, self.getCliName(vv), self.getCliHelp(vv)])
                    # did not find the name in the model lets get from schema
                    for val in x:
                        if val[1] is None or val[2] is None:
                            for kk, vv in schemaobj.iteritems():
                                # leaf node
                                if kk == "commands":
                                    for kkk, vvv in vv["properties"].iteritems():
                                        if kkk == val[0]:
                                            cliname, clihelp = self.getCliName(vvv["properties"]), self.getCliHelp(vvv["properties"])
                                            if val[1] is None:
                                                val[1] = cliname["default"]
                                            else:
                                                val[2] = clihelp["default"]

                                            cliHelpList.append((val[1], val[2]))

                                elif "properties" in vv:
                                    cliname, clihelp = self.getCliName(vv["properties"]), self.getCliHelp(vv["properties"])
                                    if val[1] is None:
                                        val[1] = cliname
                                    else:
                                        val[2] = clihelp["default"]

                                    cliHelpList.append((val[1], val[2]))
        return cliHelpList

    def isValueExpected(self, cmd, schema):
        if schema and cmd in schema:
            #sys.stdout.write("\nisValueExpected: cmd %s schema %s\n" %(cmd, schema[cmd].keys()))
            return "value" in schema[cmd]["properties"]
        return False

    def getValue(self, attribute):

        return hattribute["value"]

    def getPrompt(self, model, schema):
        try:
            return model["prompt"]
        except KeyError:
            schema["properties"]["prompt"]["default"]


    def getCliName(self, attribute):
        #sys.stdout.write("getCliName: %s\n" %(attribute,))
        return attribute["cliname"] if "cliname" in attribute else None

    def getCliHelp(self, attribute):
        return attribute["help"] if "help" in attribute else None

    def setSchema(self):

        with open(self.schemapath) as schema_data:

            self.schema = jsonref.load(schema_data)
            #pp.pprint(self.schema)


    def setModel(self):

        with open(self.modelpath, "r") as json_model_data:
            self.model = jsonref.load(json_model_data)
            #pp.pprint(self.model)

    def validateSchemaAndModel(self):
        if self.model is None or self.schema is None:
            sys.exit(2)
        else:
            try:
                # lets validate the model against the json schema
                print Draft4Validator(self.model, self.schema)
            except Exception as e:
                print e
                return False
        return True

    def display_help(self, argv):
        mline = [self.objname] + argv
        mlineLength = len(mline)

        submodel = self.model
        subschema = self.schema
        subcommands = []
        if mlineLength == 2:
            subcommands = self.getchildrenhelpcmds(mline[0], submodel, subschema)
        else:
            # advance to next submodel and subschema
            for i in range(1, mlineLength-1):
                if mline[i-1] in submodel:
                    submodelList = self.getSubCommand(mline[i], submodel[mline[i-1]]["commands"])
                    if submodelList:
                        subschemaList = self.getSubCommand(mline[i], subschema[mline[i-1]]["properties"]["commands"]["properties"])
                        for submodel, subschema in zip(submodelList, subschemaList):
                            subcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema)

        self.printCommands(mline, subcommands)

    def printCommands(self, argv, subcommands):

        mlineLength = len(argv)

        sys.stdout.write("%15s\t\t\t%s\n" %("Command", "Description"))
        sys.stdout.write("%15s\t\t\t%s\n" %("-------", "------------------"))
        if mlineLength > 2:
            for k, v in [x for x in subcommands if x[0] == argv[-2]]:
                sys.stdout.write("%15s\t\t\t%s\n" %(k, v))
                return

        # multiple commands
        for k, v in subcommands:
            sys.stdout.write("%15s\t\t\t%s\n" %(k, v))


    def default(self,):
        pass

    def do_quit(self, args):
        " Quiting FlexSwitch CLI"
        sys.stdout.write('Quiting Shell\n')
        sys.exit(0)

    def do_end(self, args):
        " Return to enable  mode"
        return

    def do_exit(self, args):

        self.prompt = self.baseprompt
        self.stop = True

    def do_where(self, args):
        def getparent(child):
            return child.parent

        completecmd = self.currentcmd
        parent = self.parent
        if parent is not None:
            completecmd = parent.currentcmd + completecmd

        # to prevent looping forever going to not accept
        # a tree larger than 10 levels
        while parent is not None:
            # root node has no parent
            # and it holds the sdk
            child = parent
            parent = getparent(child)
            if parent is not None:
                completecmd = parent.currentcmd + completecmd

        sys.stdout.write("\ncmd: %s\n\n" %(" ".join(completecmd,)))

    def precmd(self, argv):
        if len(argv) > 0:
            if argv[-1] in ('help', '?'):
                self.display_help(argv)
                return ''
        return argv
