#!/usr/bin/python
import copy
import jsonref
import sys
from jsonschema import Draft4Validator
import pprint
import requests
from tablePrint import indent, wrap_onspace_strict

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

    def getConfigObj(self):
        child = self
        config = None
        def getparent(child):
            return child.parent

        if hasattr(child, 'configList'):
            config = child

        parent = getparent(child)
        while parent is not None and config is None:
            if hasattr(parent, 'configList'):
                config = parent
            child = parent
            parent = getparent(child)


        return config

    def getSubCommand(self, key, commands):
        subList = []
        for k, v in commands.iteritems():
            #print "subCommand: key %s k %s v %s\n\n" %(key, k, v)

            if k == key:
                #sys.stdout.write("RETURN 1 %s\n\n"% (v))
                subList.append(v)
            else:
                # looking for subcommand
                if type(v) in (dict, jsonref.JsonRef):

                    if key in ('?', 'help'):
                        subList.append(v)
                    # attribute
                    elif key in v:
                        subList.append(v)
                    # model subcmd
                    elif key in [vv['cliname'] for vv in v.values() if 'cliname' in vv]:
                        subList.append(v)
                    # model command
                    elif key in [self.getCliName(vv) for kk, vv in v.iteritems() if 'commands' in kk and 'cliname' in vv]:
                        subList.append(v)
                    #elif "commands" in v and key in [self.getCliName(vv) for vv in v["commands"].values() if 'cliname' in vv]:
                    #    subList.append(v)
                    elif key in [vv['properties']['cliname']['default'] for vv in v.values() if 'properties' in vv and 'cliname' in vv['properties']]:
                        subList.append(v)
                    # schema command
                    elif key in [vv['properties']['cliname']['default'] for kk, vv in v.iteritems() if 'commands' in kk and 'properties' in vv and 'cliname' in vv['properties']]:
                        subList.append(v)
                    #elif "commands" in v and key in [vv['properties']['cliname']['default'] for vv in v["commands"]["properties"].values()]:
                    #    subList.append(v)


        return subList

    def getchildrencmds(self, parentname, model, schema):
        # working model
        #if model:
        #    return [self.getCliName(cmdobj.values()[0]) for cmdobj in [obj for k, obj in model[parentname]["commands"].iteritems() if "subcmd" in k]]
        cliNameList = []
        if schema:
            #print '\n\ngetchildrencmds: ', schema, parentname
            schemaname = self.getSchemaCommandNameFromCliName(parentname, model)
            if schemaname in schema:
                for k, schemaobj in schema[schemaname]["properties"]["commands"]["properties"].iteritems():
                    #print 'getchildrencmds: ', k, schemaobj
                    modelobj = model[schemaname]["commands"][k] if k in model[schemaname]["commands"] else None
                    #print 'getchildrencmds: ', modelobj

                    if modelobj:
                        if "subcmd" in k:
                            for kk, vv in modelobj.iteritems():
                                if 'commands' in kk:
                                    for vvv in vv.values():
                                        cliname = self.getCliName(vvv)
                                        if cliname != None:
                                            cliNameList.append(cliname)
                                else:
                                    cliname = self.getCliName(vv)
                                    if cliname != None:
                                        cliNameList.append(cliname)
                            # did not find the name in the model lets get from schema
                            # DON'T do this as the model is the master display for commands
                            #if cliname is None:
                            #    for kk, vv in schemaobj.iteritems():
                            #        cliname = self.getCliName(vv)
                        else: # just an attribute
                            for vv in modelobj.values():
                                cliname = self.getCliName(vv)
                                if cliname is not None:
                                    cliNameList.append(cliname)
        return cliNameList

    def getSchemaCommandNameFromCliName(self, cliname, model):
        #print 'getSchemaCommand:', cliname, model
        #print '\n\n'
        for key, value in model.iteritems():
            if type(value) == dict and 'cliname' in value and cliname == value['cliname']:
                #print 'getSchemaCommand found key', key
                #print '\n\n'
                return key



    def getCreateWithDefault(self, cliname, schema, model):

        schemaname = self.getSchemaCommandNameFromCliName(cliname, model)
        if schema:
            for k, schemaobj in schema[schemaname]["properties"]["commands"]["properties"].iteritems():
                if "subcmd" in k:
                   for kk in schemaobj.keys():
                       if 'createwithdefault' in kk:
                           return schemaobj[kk]['default']

        return False

    def getchildrenhelpcmds(self, parentname, model, schema):
        cliHelpList = []
        if schema:
            schemaname = self.getSchemaCommandNameFromCliName(parentname, model)
            if schemaname in schema:
                for k, schemaobj in schema[schemaname]["properties"]["commands"]["properties"].iteritems():
                    if "subcmd" in k:
                        modelobj = model[schemaname]["commands"][k] if k in model[schemaname]["commands"] else None
                        x = []
                        if modelobj:
                            for kk, vv in modelobj.iteritems():
                                # leaf node
                                if kk == "commands":
                                    for kkk, vvv in vv.iteritems():
                                        x.append([kkk, self.getCliName(vvv), self.getCliHelp(vvv)])
                                elif type(vv) == dict:
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

                                    elif "properties" in vv and "commands" in vv["properties"]:
                                        cliname, clihelp = self.getCliName(vv["properties"]), self.getCliHelp(vv["properties"])
                                        if val[1] is None and cliname:
                                            val[1] = cliname
                                        elif clihelp:
                                            val[2] = clihelp["default"]
                                        if val[1] and val[2]:
                                            cliHelpList.append((val[1], val[2]))
        return cliHelpList

    def isValueExpected(self, cmd, model, schema):
        schemaname = self.getSchemaCommandNameFromCliName(cmd, model)
        #print 'isValueExpected', schema, schemaname
        if schema:
            if schemaname in schema:
                #sys.stdout.write("\nisValueExpected: cmd %s schema %s\n" %(cmd, schema[schemaname].keys()))
                return "value" in schema[schemaname]["properties"]
        return False

    def getValue(self, attribute):

        return attribute["value"]

    def getPrompt(self, model, schema):
        try:
            return model["prompt"]
        except KeyError:
            schema["properties"]["prompt"]["default"]


    def getCliName(self, attribute):
        #print 'getCliName xxx:', attribute, type(attribute), 'cliname' in attribute, attribute["cliname"]
        return attribute["cliname"] if ((type(attribute) == dict) and ("cliname" in attribute)) else None

    def getCliHelp(self, attribute):
        return attribute["help"] if type(attribute) == dict and "help" in attribute else None

    def setSchema(self):

        with open(self.schemapath) as schema_data:

            self.schema = jsonref.load(schema_data)
            # ENABLE THIS if you see problems with decode
            #pp.pprint(self.schema)


    def setModel(self):

        with open(self.modelpath, "r") as json_model_data:
            self.model = jsonref.load(json_model_data)
            # ENABLE THIS if you see problems with decode
            #pp.pprint(self.model)

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
                    schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], submodel)
                    submodelList = self.getSubCommand(mline[i], submodel[schemaname]["commands"])
                    if submodelList:
                        subschemaList = self.getSubCommand(mline[i], subschema[schemaname]["properties"]["commands"]["properties"])
                        for submodel, subschema in zip(submodelList, subschemaList):
                            subcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema)

        self.printCommands(mline, subcommands)

    def printCommands(self, argv, subcommands):

        labels = ('Command', 'Description',)
        rows = []
        for x in subcommands:
            rows.append((x[0], x[1]))
        width = 30
        print indent([labels]+rows, hasHeader=True, separateRows=False,
                     prefix=' ', postfix=' ', headerChar= '-', delim='    ',
                     wrapfunc=lambda x: wrap_onspace_strict(x,width))

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

    def do_apply(self, argv):
        configObj = self.getConfigObj()
        if configObj:
            configObj.do_apply(argv)

    def do_showunapplied(self, argv):
        configObj = self.getConfigObj()
        if configObj:
            configObj.do_showunapplied(argv)


    def do_clearunapplied(self, argv):
        configObj = self.getConfigObj()
        if configObj:
            configObj.do_clearunapplied(argv)

        # need to ensure that we exit out of current config if we are
        # not already at config
        child = self
        if child.objname != "config":
            parent = child.parent
            while parent is not None:
                if parent.objname == "config":
                    self.do_exit([])
                    parent = None
                else:
                    self.do_exit([])
                    child = parent
                    parent = child.parent


    def precmd(self, argv):
        if len(argv) > 0:
            if argv[-1] in ('help', '?'):
                self.display_help(argv)
                return ''
        return argv
