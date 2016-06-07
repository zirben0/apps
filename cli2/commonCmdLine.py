#!/usr/bin/python
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
import snapcliconst
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

# this is not a terminating command
SUBCOMMAND_VALUE_NOT_EXPECTED = 1
# this is a terminating command which expects a value from user
SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE = 2
# this is a terminating command but no value is necessary
SUBCOMMAND_VALUE_EXPECTED = 3


class CommonCmdLine(object):

    configDict = {}
    def __init__(self, parent, switch_ip, schema_path, model_path, layer):
        if not USING_READLINE:
            self.completekey = None
        self.objname = None
        # dependency on CmdLine that these are set after the init
        #self.sdk = None
        #self.sdkshow = None
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

    def getRootAttr(self, attr):
        parent = self.parent
        child = self

        def getparent(child):
            return child.parent

        # to prevent looping forever going to not accept
        # a tree larger than 10 levels
        rootAttr = None
        while rootAttr is None:
            # root node has no parent
            # and it holds the sdk
            if parent is None:
                rootAttr = getattr(child, attr)
            else:
                child = parent

            if not rootAttr:
                parent = getparent(child)
        return rootAttr

    def getSdk(self):
        return self.getRootAttr('sdk')

    def getSdkShow(self):
        return self.getRootAttr('sdkshow')

    def getShowObj(self,):
        return self.getObjByInstanceType('ShowCmd')

    def getConfigObj(self):
        return self.getObjByInstanceType('ConfigCmd')

    def getRootObj(self):
        return self.getObjByInstanceType('CmdLine')

    def getObjByInstanceType(self, instname):
        """
        Get object by walking the tree to find the instance
        For now we are using this to find the instance who
        has the attribute configList which contains all
        the config entries
        :return:
        """
        child = self
        config = None
        def getparent(child):
            return child.parent
        if child.__class__.__name__ == instname:
            config = child

        parent = getparent(child)
        while parent is not None and config is None:
            if parent.__class__.__name__ == instname:
                config = parent
            child = parent
            parent = getparent(child)
        return config

    # TODO write more readable logic to get a model commands sub command obj
    # This is a critical function as all complete_, and do_ functions use
    # this
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
                            listattrDict = dict(v['listattrs']) if 'listattrs' in v else {}
                            for kk, vv in v.iteritems():
                                if 'commands' in kk and 'properties' in vv and 'cliname' not in vv['properties']:
                                    for kkk, vvv in vv['properties'].iteritems():
                                        if 'subcmd' in kkk:
                                            # all commands are subcmds
                                            for kkkk, vvvv in vvv.iteritems():
                                                if kkkk == key:
                                                    subList.append(vvv)
                                                elif 'properties' in vvvv and 'cliname' in vvvv['properties'] and key == vvvv['properties']['cliname']['default']:
                                                    subList.append(vvv)
                                            # sub commands part of a leaf
                                            #elif kkk in listattrDict:
                                            #    subList.append(vvv)

                                elif 'commands' in kk and 'cliname' not in vv:
                                    for kkk, vvv in vv.iteritems():
                                        if 'subcmd' in kkk:
                                            # all commands are subcmds
                                            for kkkk, vvvv in vvv.iteritems():
                                                if kkk == key:
                                                    subList.append(vvv)
                                                elif 'cliname' in vvvv and key == vvvv['cliname']:
                                                    subList.append(vvv)
                                            # sub commands part of a leaf
                                            #elif kkk in listattrDict:
                                            #    subList.append(vvv)

                                elif kk == key:
                                    subList.append(vv)

        return subList

    def getchildrencmds(self, parentname, model, schema):
        cliNameList = []
        if schema:
            schemaname = self.getSchemaCommandNameFromCliName(parentname, model)
            if schemaname in schema:
                for k, schemaobj in snapcliconst.GET_SCHEMA_COMMANDS(schemaname, schema).iteritems():
                    modelobj = snapcliconst.GET_MODEL_COMMANDS(schemaname, model)[k] \
                                    if k in snapcliconst.GET_MODEL_COMMANDS(schemaname, model) else None
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
            for k, schemaobj in snapcliconst.GET_SCHEMA_COMMANDS(schemaname, schema).iteritems():
                if "subcmd" in k:
                   for kk in schemaobj.keys():
                       if 'createwithdefault' in kk:
                           return schemaobj[kk]['default']

        return False

    def getchildrenhelpcmds(self, parentname, model, schema):
        cliHelpList = [["<cr>", ""]]
        if schema:
            schemaname = self.getSchemaCommandNameFromCliName(parentname, model)
            for k, schemaobj in snapcliconst.GET_SCHEMA_COMMANDS(schemaname, schema).iteritems():
                if "subcmd" in k:
                    modelobj = snapcliconst.GET_MODEL_COMMANDS(schemaname, model)[k] \
                                if k in snapcliconst.GET_MODEL_COMMANDS(schemaname, model) else None
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

                                                if val[1] != parentname:
                                                    cliHelpList.append((val[1], val[2]))
                                elif "properties" in vv and "commands" in vv["properties"]:
                                    # todo need to get proper parsing to find the help
                                    cliname, clihelp = self.getCliName(vv["properties"]), self.getCliHelp(vv["properties"])
                                    if val[1] is None and cliname:
                                        val[1] = cliname
                                    elif clihelp:
                                        val[2] = clihelp["default"]
                                    if val[1] != parentname:
                                        cliHelpList.append((val[1], val[2]))
                        else:
                            cliHelpList.append((val[1], val[2]))
        return cliHelpList

    def getValueMinMax(self, cmd, model, schema):
        schemaname = self.getSchemaCommandNameFromCliName(cmd, model)
        if schema:
            if schemaname in schema and \
                "properties" in schema[schemaname] and \
                    "value" in schema[schemaname]["properties"] and \
                    'properties' in schema[schemaname]['properties']['value']:
                keys = [k for k, v in schema[schemaname]['properties']['value']['properties'].iteritems() if type(v) in (dict, jsonref.JsonRef)]
                #objname = schema[schemaname]['properties']['objname']['default']
                #sys.stdout.write("\nisValueExpected: cmd %s objname %s flex keys %s %s\n" %(cmd, objname, keys, schema[schemaname]['properties']['value']['properties']))
                minmax = [(v['properties']['argtype']['minimum'],
                           v['properties']['argtype']['maximum']) for k, v in schema[schemaname]['properties']['value']['properties'].iteritems()
                                            if 'properties' in v and 'argtype' in v['properties'] and 'minimum' in v['properties']['argtype'] and k in keys]
                if minmax:
                    return minmax[0]
        return None, None

    def getValueSelections(self, cmd, model, schema):
        schemaname = self.getSchemaCommandNameFromCliName(cmd, model)
        if schema:
            if schemaname in schema and \
                "properties" in schema[schemaname] and \
                    "value" in schema[schemaname]["properties"] and \
                    'properties' in schema[schemaname]['properties']['value']:
                keys = [k for k, v in schema[schemaname]['properties']['value']['properties'].iteritems() if type(v) in (dict, jsonref.JsonRef)]
                objname = schema[schemaname]['properties']['objname']['default']
                #sys.stdout.write("\nisValueExpected: cmd %s objname %s flex keys %s %s\n" %(cmd, objname, keys, schema[schemaname]['properties']['value']['properties']))
                selections = [v['properties']['argtype']['enum'] for k, v in schema[schemaname]['properties']['value']['properties'].iteritems()
                                            if 'properties' in v and 'argtype' in v['properties'] and 'enum' in v['properties']['argtype'] and k in keys]
                if selections:
                    return selections[0]
        return []

    def commandAttrsLoop(self, modelcmds, schemacmds):
        for attr, val in modelcmds.iteritems():
            yield (attr, val), (attr, schemacmds[attr])

    def isCommandLeafAttrs(self, modelcmds, schemacmds):
        return "commands" in modelcmds and "commands" in schemacmds

    def isLeafValueExpected(self, cliname, modelcmds, schemacmds):
        keys = []
        objname = None
        expected = SUBCOMMAND_VALUE_NOT_EXPECTED
        help = ''
        for (mattr, mattrval), (sattr, sattrval) in self.commandAttrsLoop(modelcmds["commands"], schemacmds["commands"]["properties"]):
            if sattrval['properties']['key']['default']:
                keys.append(sattr)

            if 'cliname' in mattrval and mattrval['cliname'] == cliname:
                help = ''
                if 'enum' in sattrval['properties']['argtype']:
                    help = "/".join(sattrval['properties']['argtype']['enum']) + '\n'
                    if len(sattrval['properties']['argtype']['enum']) == 2:
                        expected = SUBCOMMAND_VALUE_EXPECTED
                if 'type' in sattrval['properties']['argtype'] and \
                        snapcliconst.isboolean(sattrval['properties']['argtype']['type']):
                    expected = SUBCOMMAND_VALUE_EXPECTED

                objname = schemacmds['objname']['default']
                help += sattrval['properties']['help']['default']
        return (expected, objname, keys, help)


    def getModelDefaultAttrVal(self, argv, schemaname, model, schema, delcmd=False):

        # touching an attribute within this command tree, but we need to find out which subcmd contains
        # the attribute
        for modelkeys, modelcmds in snapcliconst.GET_MODEL_COMMANDS(schemaname, model).iteritems():
            schemacmds = snapcliconst.GET_SCHEMA_COMMANDS(schemaname, schema)[modelkeys]
            #leaf attr model
            if self.isCommandLeafAttrs(modelcmds,schemacmds):
                for (mattr, mattrval), (sattr, sattrval) in self.commandAttrsLoop(modelcmds["commands"], schemacmds["commands"]["properties"]):
                    if 'cliname' in mattrval and mattrval['cliname'] == argv[0]:
                        isDefaultSet = snapcliconst.getSchemaCommandAttrIsDefaultSet(sattrval)
                        defaultArg = snapcliconst.getSchemaCommandAttrDefaultArg(sattrval)
                        # we want opposite of default if boolean delete
                        # lets do the opposite of default value if enums length is 2
                        # or if we have a boolean value.
                        # this helps when setting string based boolean values
                        argtype = snapcliconst.getValueArgumentType(sattrval)
                        selections = snapcliconst.getValueArgumentSelections(sattrval)
                        if selections and \
                                argtype and \
                            snapcliconst.isSelectionTypeNotNeeded(selections, argtype):

                            if delcmd:
                                # lets determine the value based on whether this is a delcmd
                                # or not
                                # special case hack!!!
                                if mattrval['cliname'] in ('shutdown', ):
                                    rv = list(frozenset([str(x).lower() for x in selections]).intersection(snapcliconst.CLI_COMMAND_POSITIVE_TRUTH_VALUES))
                                    for k in selections:
                                        if rv and k.lower() == rv[0]:
                                            return k

                                else:
                                    rv = list(frozenset([str(x).lower() for x in selections]).itersection(snapcliconst.CLI_COMMAND_NEGATIVE_TRUTH_VALUES))
                                    for k in selections:
                                        if rv and k.lower() == rv[0]:
                                            return k
                            else:
                                # lets determine the value based on whether this is a delcmd
                                # or not
                                # special case hack!!!
                                if mattrval['cliname'] in ('shutdown', ):
                                    rv = list(frozenset([str(x).lower() for x in selections]).intersection(snapcliconst.CLI_COMMAND_NEGATIVE_TRUTH_VALUES))
                                    for k in selections:
                                        if rv and k.lower() == rv[0]:
                                            return k
                                else:
                                    rv = list(frozenset([str(x).lower() for x in selections]).itersection(snapcliconst.CLI_COMMAND_POSITIVE_TRUTH_VALUES))
                                    for k in selections:
                                        if rv and  k.lower() == rv[0]:
                                            return k
                            return None
                        elif snapcliconst.isboolean(argtype):

                            if delcmd:
                                rv = False
                            else:
                                rv = True
                            return rv

                        # setting default value
                        return defaultArg if isDefaultSet else None
        return None

    def isValueExpected(self, cmd, model, schema):
        '''
        Function used by most complete functions to determine based on the cmd
        and model/schema if a value is needed by the user or if the next cmd
        is another command.  If a value is expected this function may
        return valid values from model enums, so that the user knows what to
        add in the case an attribute is a selection attribute.
        :param cmd:
        :param model:
        :param schema:
        :return:
        '''

        schemaname = self.getSchemaCommandNameFromCliName(cmd, model)
        if schema and schemaname in schema:
            schemaValues = snapcliconst.getValueInSchema(schema[schemaname])
            if schemaValues:
                keys = [k for k, v in schemaValues.iteritems() if type(v) in (dict, jsonref.JsonRef)]
                help = ''
                expected = SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE
                for k, v in schemaValues.iteritems():
                    argtype = snapcliconst.getValueArgumentType(v)
                    enums = snapcliconst.getValueArgumentSelections(v)
                    if enums:
                        help = "/".join(enums) + '\n'
                        # special case don't need a value (default will be taken when applied)
                        if not snapcliconst.isSelectionTypeNotNeeded(enums, argtype):
                            expected  = SUBCOMMAND_VALUE_EXPECTED
                    elif argtype:
                        if snapcliconst.isboolean(argtype):
                            expected = SUBCOMMAND_VALUE_EXPECTED

                objname = snapcliconst.getSchemaObjName(schemaname, schema)
                help += snapcliconst.getHelp(schemaname, model, schema)

                return (expected, objname, keys, help)

                # lets check to see if this schema is a command attribute schema
        return (SUBCOMMAND_VALUE_NOT_EXPECTED, None, [], "")

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
        helpcommands = []
        if mlineLength == 1:
            helpcommands = self.getchildrenhelpcmds(self.objname, submodel, subschema)

        # advance to next submodel and subschema
        for i in range(1, mlineLength):
            if mline[i-1] in submodel:
                schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], submodel)
                if schemaname:
                    submodelList, subschemaList = self.getSubModelSubSchemaListFromCommand(mline[i],
                                                                                      snapcliconst.GET_MODEL_COMMANDS(schemaname, submodel),
                                                                                      snapcliconst.GET_SCHEMA_COMMANDS(schemaname, subschema))
                    if submodelList and subschemaList:
                        for submodel, subschema in zip(submodelList, subschemaList):
                            (valueexpected, objname, keys, help) = self.isValueExpected(mline[i], submodel, subschema)
                            if i == mlineLength - 1:
                                if valueexpected != SUBCOMMAND_VALUE_NOT_EXPECTED:
                                    cmd = " ".join(argv[:-1])
                                    helpcommands = [[cmd, help]]
                                else:
                                    helpcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema)
                    else:
                        if 'commands' in model[schemaname]:
                            for mcmd, mcmdvalues in submodel[schemaname]['commands'].iteritems():
                                scmdvalues = subschema[schemaname]['properties']['commands']['properties'][mcmd]
                                if 'subcmd' in mcmd:
                                    if self.isCommandLeafAttrs(mcmdvalues, scmdvalues):
                                        if i == (mlineLength - 1): # value expected from attrs
                                            # reached attribute values
                                            for attr, attrvalue in mcmdvalues['commands'].iteritems():
                                                if attrvalue['cliname'] == mline[i]:
                                                    sattrvalue = scmdvalues['commands']['properties'][attr]
                                                    subcommands.append([snapcliconst.getAttrCliName(attrvalue, sattrvalue),
                                                                       snapcliconst.getAttrHelp(attrvalue, sattrvalue)])

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
            # lets move user back to config base
            # once the apply command has been entered
            if not self.__class__.__name__ ==  "ConfigCmd":
                self.do_exit(argv)

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

    def do_version(self, argv):
        '''
        Show cli version and flexswitch version
        :param argv:
        :return:
        '''
        rootObj = self.getRootObj()
        if rootObj:
            rootObj.sdkshow.printSystemSwVersionStates()

    def precmd(self, argv):
        if len(argv) > 0:
            if argv[-1] in ('help', '?'):
                self.display_help(argv)
                return ''
        return argv
