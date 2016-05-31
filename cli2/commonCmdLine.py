#!/usr/lib/python
#
#Copyright [2016] [SnapRoute Inc]
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#       Unless required by applicable law or agreed to in writing, software
#       distributed under the License is distributed on an "AS IS" BASIS,
#       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#       See the License for the specific language governing permissions and
#       limitations under the License.
#
# _______  __       __________   ___      _______.____    __    ____  __  .___________.  ______  __    __
# |   ____||  |     |   ____\  \ /  /     /       |\   \  /  \  /   / |  | |           | /      ||  |  |  |
# |  |__   |  |     |  |__   \  V  /     |   (----` \   \/    \/   /  |  | `---|  |----`|  ,----'|  |__|  |
# |   __|  |  |     |   __|   >   <       \   \      \            /   |  |     |  |     |  |     |   __   |
# |  |     |  `----.|  |____ /  .  \  .----)   |      \    /\    /    |  |     |  |     |  `----.|  |  |  |
# |__|     |_______||_______/__/ \__\ |_______/        \__/  \__/     |__|     |__|      \______||__|  |__|
#
# Class contains common methods used the various tree elements of the cli.
#
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

    def getSubCommand(self, commandkey, commands, model=None):
        subList = []
        key = commandkey
        if model and type(model) in (dict, jsonref.JsonRef):
            #print 'getSubCmd: searchKey %s\n' % (k,)
            key = self.getSchemaCommandNameFromCliName(commandkey, model)
            if not key:
                if 'commands' in model:
                    for cmd, submodel in model["commands"].iteritems():
                        #print 'getSubCommand: cmd ', cmd, submodel
                        if 'subcmd' in cmd and key is None:
                            key = self.getSchemaCommandNameFromCliName(commandkey, submodel)
                if [x for x in model.keys() if 'subcmd' in x]:
                    for cmd, submodel in model.iteritems():
                        #print 'getSubCommand: cmd ', cmd, submodel
                        if type(submodel) in (dict, jsonref.JsonRef):
                            if [y for y in submodel.values() if 'cliname' in y] and key is None:
                                key = self.getSchemaCommandNameFromCliName(commandkey, submodel)

            if not key:
                key = commandkey

        if type(commands) in (dict, jsonref.JsonRef):
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
                        #    subList.append(v
                        elif 'subcmd' in k:
                            for kk, vv in v.iteritems():
                                if 'commands' in kk and 'properties' in vv and 'cliname' not in vv['properties']:
                                    for kkk, vvv in vv['properties'].iteritems():
                                        if 'subcmd' in kkk:
                                            for kkkk, vvvv in vvv.iteritems():
                                                if 'properties' in vvvv and 'cliname' in vvvv['properties'] and key == vvvv['properties']['cliname']['default']:
                                                    subList.append(vvv)
                                elif 'commands' in kk and 'cliname' not in vv:
                                    for kkk, vvv in vv.iteritems():
                                        if 'subcmd' in kkk:
                                            for kkkk, vvvv in vvv.iteritems():
                                                if 'cliname' in vvvv and key == vvvv['cliname']:
                                                    subList.append(vvv)
                                elif kk == key:
                                    subList.append(vv)



        return subList

    def getchildrencmds(self, parentname, model, schema):
        # working model
        #if model:
        #    return [self.getCliName(cmdobj.values()[0]) for cmdobj in [obj for k, obj in model[parentname]["commands"].iteritems() if "subcmd" in k]]
        cliNameList = []
        if schema:
            #print '\n\ngetchildrencmds: ', schema, parentname
            schemaname = self.getSchemaCommandNameFromCliName(parentname, model)
            #print '\n\ngetchildrencmds: ', schemaname
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
                        elif type(modelobj) in (dict, jsonref.JsonRef): # just an attribute
                            for vv in modelobj.values():
                                cliname = self.getCliName(vv)
                                if cliname is not None:
                                    cliNameList.append(cliname)
        return cliNameList

    def getSchemaCommandNameFromCliName(self, cliname, model):
        for key, value in model.iteritems():
            if type(value) in (dict, jsonref.JsonRef):
                # branch
                if 'cliname' in value and cliname == value['cliname']:
                    return key
                else: # leaf
                    for k, v in value.iteritems():
                        if 'commands' in k:
                            if type(v) in (dict, jsonref.JsonRef):
                                for kk, vv in v.iteritems():
                                    if 'subcmd' in kk:
                                        return self.getSchemaCommandNameFromCliName(cliname, vv)
                                    else:
                                        if 'cliname' in vv and cliname == vv['cliname']:
                                            return kk
                        else:
                            if type(v) in (dict, jsonref.JsonRef):
                                for kk, vv in v.iteritems():
                                    if 'cliname' in vv and cliname == vv['cliname']:
                                        return kk

        return None


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
                        if modelobj and type(modelobj) in (dict, jsonref.JsonRef):
                            listattrDict = {}
                            if 'listattrs' in modelobj:
                                listattrDict = dict(modelobj['listattrs'])
                            for kk, vv in modelobj.iteritems():
                                # leaf node
                                if kk == "commands":
                                    for kkk, vvv in vv.iteritems():
                                        if kkk in listattrDict:
                                            if type(vvv) in (dict, jsonref.JsonRef):
                                                for kkkk, vvvv in vvv.iteritems():
                                                    if 'cliname' in vvvv.keys():
                                                        x.append([listattrDict[kkk], vvvv['cliname'], None])
                                        else:
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
                                                if "properties" in vvv:
                                                    cliname, clihelp = self.getCliName(vvv["properties"]), self.getCliHelp(vvv["properties"])
                                                    if val[1] is None:
                                                        val[1] = cliname["default"]
                                                    else:
                                                        val[2] = clihelp["default"]

                                                    cliHelpList.append((val[1], val[2]))
                                    elif "properties" in vv and "commands" in vv["properties"]:
                                        # todo need to get proper parsing to find the help
                                        cliname, clihelp = self.getCliName(vv["properties"]), self.getCliHelp(vv["properties"])
                                        if val[1] is None and cliname:
                                            val[1] = cliname
                                        elif clihelp:
                                            val[2] = clihelp["default"]
                                        cliHelpList.append((val[1], val[2]))
                            else:
                                cliHelpList.append((val[1], val[2]))
        return cliHelpList

    def getValueSelections(self, cmd, model, schema):
        schemaname = self.getSchemaCommandNameFromCliName(cmd, model)
        if schema:
            if schemaname in schema and \
                "properties" in schema[schemaname] and \
                    "value" in schema[schemaname]["properties"] and \
                    'properties' in schema[schemaname]['properties']['value']:
                keys = [k for k, v in schema[schemaname]['properties']['value']['properties'].iteritems() if type(v) in (dict, jsonref.JsonRef)]
                objname = schema[schemaname]['properties']['objname']['default']
                #sys.stdout.write("\nisValueExpected: cmd %s objname %s flex keys %s\n" %(cmd, objname, keys))
                if 'argtype' in schema[schemaname]['properties']['value']['properties']['argtype'] \
                    and 'enum' in schema[schemaname]['properties']['value']['properties']['argtype']:
                    return schema[schemaname]['properties']['value']['properties']['argtype']['enum']
        return []

    def isValueExpected(self, cmd, model, schema):
        schemaname = self.getSchemaCommandNameFromCliName(cmd, model)
        #print 'isValueExpected', schema, schemaname
        if schema:
            if schemaname in schema and \
                "properties" in schema[schemaname] and \
                    "value" in schema[schemaname]["properties"] and \
                    'properties' in schema[schemaname]['properties']['value']:
                keys = [k for k, v in schema[schemaname]['properties']['value']['properties'].iteritems() if type(v) in (dict, jsonref.JsonRef)]
                help = ''
                for k, v in schema[schemaname]['properties']['value']['properties'].iteritems():
                    if 'properties' in v and 'argtype' in v['properties'] and 'enum' in v['properties']['argtype']:
                        help = "/".join(v['properties']['argtype']['enum']) + '\n'

                objname = schema[schemaname]['properties']['objname']['default']
                help += schema[schemaname]['properties']['help']['default']
                #sys.stdout.write("\nisValueExpected: cmd %s objname %s flex keys %s\n" %(cmd, objname, keys))
                return (True, objname, keys, help)
        return (False, None, [], "")

    def getValue(self, attribute):

        return attribute["value"]

    def getPrompt(self, model, schema):
        try:
            return model["prompt"]
        except KeyError:
            return None


    def getCliName(self, attribute):
        #print 'getCliName xxx:', attribute, type(attribute), 'cliname' in attribute, attribute["cliname"]
        return attribute["cliname"] if ((type(attribute) == dict) and ("cliname" in attribute)) else None

    def getCliHelp(self, attribute):
        return attribute["help"] if type(attribute) == dict and "help" in attribute else None

    def setSchema(self):

        with open(self.schemapath, 'r') as schema_data:

            self.schema = jsonref.load(schema_data)
            # ENABLE THIS if you see problems with decode
            #pp.pprint(self.schema)


    def setModel(self):

        with open(self.modelpath, "rw+") as json_model_data:
            self.model = jsonref.load(json_model_data)
            # ENABLE THIS if you see problems with decode
            #pp.pprint(self.model)

    def getSubModelSubSchemaListFromCommand(self, command, submodel, subschema):
        submodelList, subschemaList = self.getSubCommand(command, submodel), \
                            self.getSubCommand(command, subschema, submodel)
        if submodelList and subschemaList:
            return submodelList, subschemaList
        return [], []

    def display_help(self, argv):
        mline = [self.objname] + argv[:-1]
        mlineLength = len(mline)
        submodel = self.model
        subschema = self.schema
        subcommands = []

        # advance to next submodel and subschema
        for i in range(1, mlineLength):
            if mline[i-1] in submodel:
                schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], submodel)
                if schemaname:
                    submodelList, subschemaList = self.getSubModelSubSchemaListFromCommand(mline[i],
                                                                                      submodel[schemaname]["commands"],
                                                                                      subschema[schemaname]["properties"]["commands"]["properties"])
                    for submodel, subschema in zip(submodelList, subschemaList):
                        (valueexpected, objname, keys, help) = self.isValueExpected(mline[i], submodel, subschema)
                        if i == mlineLength - 1:
                            if valueexpected:
                                cmd = " ".join(argv[:-1])
                                helpcommands = [[cmd, help]]
                            else:
                                helpcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema)

        self.printCommands(mline, helpcommands)

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
