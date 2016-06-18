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
# This is a leaf node which should handle command attributes related to a leaf model
#
import sys
import cmdln
import json
import jsonref
import string
import snapcliconst
from sets import Set
from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine, SUBCOMMAND_VALUE_NOT_EXPECTED, \
    SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE, SUBCOMMAND_VALUE_EXPECTED
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
    '''
    this class is the command attribute container for a given schema objects children
    The caller of this class is a config key.

    For example:
     parent config: interface ethernet 10
     this object will allow the user to fill in commands whose schema is related to
     an ethernet interface.  It is important to know that if the user wants this attribute
     to apply to another model then the attribute name must be the same. 'ethernet' in
     this example.
    '''

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
        self.parentcliname = cliname
        # variable used to determine that when set the attribute being set is a key for an object
        self.subcommand = False
        self.issubcommandlist = False

        self.objDict = {}

        self.setupCommands()

    def applybaseconfig(self, cliname):
        '''
        Function is called to apply the command used when creating this class.
        Basically this should mean that a KEY for a given object / command is being
        created.
        :param cliname:
        :return:
        '''
        def getParentConfigEntry(configObj, objname, keyvalueDict): #parentattr, parentval):

            for config in configObj.configList:
                if config.name == objname:
                    # todo need to check keys
                    numKeys = len(keyvalueDict)
                    keysfoundcnt = 0

                    if len(config.attrList) == 0:
                        return config

                    for entry in config.attrList:

                        lencurrkeys = len([x for x in config.attrList if entry.isKey()])
                        # lets update the entry because we now have more keys
                        if lencurrkeys < numKeys:
                            if entry.isKey() and \
                                (entry.attr in keyvalueDict and
                                    (entry.val == keyvalueDict[entry.attr][0] or
                                     entry.val in (snapcliconst.CLI_COMMAND_NEGATIVE_TRUTH_VALUES +
                                                   snapcliconst.CLI_COMMAND_POSITIVE_TRUTH_VALUES))):
                                return config
                        # found an entry with same amount of keys
                        elif lencurrkeys == numKeys:
                            # all key values must be set for config to be found
                            if entry.isKey() and \
                                (entry.attr in keyvalueDict and
                                    (entry.val == keyvalueDict[entry.attr][0] or
                                     entry.val in (snapcliconst.CLI_COMMAND_NEGATIVE_TRUTH_VALUES +
                                                   snapcliconst.CLI_COMMAND_POSITIVE_TRUTH_VALUES))):
                                keysfoundcnt += 1

                            if keysfoundcnt == numKeys:
                                return config
            return None

        def createChildTreeObjectsDict(objcmds):
            objDict = {}
            # lets fill out the object to attributes mapping valid for this level in the tree
            for cmds in objcmds:
                if type(cmds) in (dict, jsonref.JsonRef):
                    for k, v in cmds.iteritems():
                        if v['objname'] not in objDict:
                            objDict[v['objname']] = {}

                        objDict[v['objname']].update({k:v})
            return objDict

        def getCurrentLeafContainerKeyValues(cmdtype, parent, currentcmd, delete, defaultValFunc):
            """
            Two cases for a command in a leaf
            1) leaf container - example interface eth 0
            2) sub leaf container example interface eth 0
                                            - spanning_tree brg_vlan
            :param parent:
            :param currentcmd:
            :return:
            """
            keyvalueDict = {}
            if len(currentcmd) == 0:
                basekey = parent.lastcmd[-2]  if snapcliconst.COMMAND_TYPE_CONFIG_NOW not in cmdtype else parent.lastcmd[-1]
                basevalue = parent.lastcmd[-1]  if snapcliconst.COMMAND_TYPE_CONFIG_NOW not in cmdtype else defaultValFunc([basekey], delcmd=delete)
                keyvalueDict.update({basekey: (basevalue, parent.lastcmd)})
            else:
                basekey = currentcmd[-2] if snapcliconst.COMMAND_TYPE_CONFIG_NOW not in cmdtype else currentcmd[-1]
                basevalue = currentcmd[-1] if snapcliconst.COMMAND_TYPE_CONFIG_NOW not in cmdtype else defaultValFunc([basekey], delcmd=delete)
                keyvalueDict.update({basekey: (basevalue, currentcmd)})
                if hasattr(parent, 'parent') and parent.parent:
                    keyvalueDict.update(getCurrentLeafContainerKeyValues(cmdtype, parent.parent, parent.currentcmd, delete, defaultValFunc))

            return keyvalueDict

        self.objDict = {}
        configObj = self.getConfigObj()
        for model, schema in zip(self.modelList, self.schemaList):

            listAttrs = model[self.objname]['listattrs'] if 'listattrs' in model[self.objname] else []
            # lets get all command objects for the given command
            allCmdsList = self.prepareConfigTreeObjects(None,
                                                        self.objname,
                                                        False,
                                                        model[self.objname]['cliname'],
                                                        model[self.objname]["commands"],
                                                        schema[self.objname]["properties"]["commands"]["properties"],
                                                        listAttrs)

            # lets fill out the object to attributes mapping valid for this level in the tree
            self.objDict = createChildTreeObjectsDict(allCmdsList)

            if configObj:
                delete = True if snapcliconst.COMMAND_TYPE_DELETE in self.cmdtype else False

                # get the current leaf container key value
                keyvalueDict = getCurrentLeafContainerKeyValues(self.cmdtype,
                                                                self.parent,
                                                                self.currentcmd,
                                                                delete,
                                                                self.getCommandDefaultAttrValue)

                # lets go through the valid sub tree command objects
                # and fill in what command was entered by the user
                for objname, objattrs in self.objDict.iteritems():

                    config = None
                    # show commands don't require keys because we
                    # may be doing a get all so lets treat show as a
                    # special case.
                    if snapcliconst.COMMAND_TYPE_SHOW not in self.cmdtype:
                        # get the parent object if this is a sub command
                        # as this may be a secondary key for the object
                        if self.parent:
                            config = getParentConfigEntry(configObj, objname, keyvalueDict)
                        if not config:
                            config = CmdEntry(self, objname, self.objDict[objname])

                        if cliname in keyvalueDict:
                            # total keys must be provisioned for config to be valid
                            # the keyvalueDict may contain more tree keys than is applicable for the
                            # config tree
                            objkeyslen = len([(k, v) for k, v in objattrs.iteritems()
                                                                if v['isattrkey'] and v['createwithdefaults']])
                            isvalid = len(keyvalueDict) >= objkeyslen and objkeyslen != 0

                            isValidKeyConfig = len([(k, v) for k, v in objattrs.iteritems() if v['isattrkey']
                                                                         and (k in keyvalueDict)]) > 0
                            # we want a full key config
                            if isValidKeyConfig:
                                for basekey, (basevalue, cmd) in keyvalueDict.iteritems():
                                    if basekey in objattrs:
                                        if objattrs[basekey]['isattrkey']:
                                            config.setDelete(delete)

                                        # all keys for an object must be set and
                                        # and all all attributes must have default values
                                        # in order for the object to be considered valid and
                                        # ready to be provisioned.
                                        config.setValid(isvalid)
                                        config.set(cmd, delete, basekey, basevalue, isKey=objattrs[basekey]['isattrkey'])
                            else:
                                isvalid = len([(k, v) for k, v in objattrs.iteritems() if v['isattrkey'] and
                                                                               v['createwithdefaults'] and
                                                                              (v['value']['default'])]) > 0

                                # rare case that an attribute of an object is used as a key
                                # but found that it does exist as is the case for router bgp ....
                                isObjNonKeyConfig = len([(k, v) for k, v in objattrs.iteritems() if not v['isattrkey']
                                                                         and k in keyvalueDict]) > 0
                                if isObjNonKeyConfig:
                                    for basekey, (basevalue, cmd) in keyvalueDict.iteritems():
                                        if basekey in objattrs:
                                            if objattrs[basekey]['isattrkey']:
                                                config.setDelete(delete)
                                            # values supplied may not be the object key but they were used
                                            # to create the object as is the case with router bgp
                                            config.setValid(isvalid)
                                            config.set(cmd, delete, basekey, basevalue, isKey=True)
                    else:
                        config = CmdEntry(self, objname, self.objDict[objname])
                        config.setValid(True)

                    # only add this config if it does not already exist
                    cfg = configObj.doesConfigExist(config)
                    if not cfg:
                        configObj.configList.append(config)
                    elif cfg and snapcliconst.COMMAND_TYPE_DELETE in self.cmdtype:
                        # let remove the previous command if it was set
                        # or lets delete the config
                        if len(config.attrList) == len(keyvalueDict):
                            try:
                                # lets remove this command
                                # because basically the user cleared
                                # the previous unapplied command
                                configObj.configList.remove(cfg)
                                return False
                            except ValueError:
                                pass
        return True if snapcliconst.COMMAND_TYPE_CONFIG_NOW not in self.cmdtype else False

    def getCmdKeysToIgnore(self, objname, schema):
        '''
        Ignore an objects value keys because they were used to get to a config mode. And should
        not be displayed as part of the config help or <tab> completion
        '''
        ignoreKeys = []
        if objname in schema and \
                'properties' in schema[objname] and \
                'value' in schema[objname]['properties'] and \
                'properties' in schema[objname]['properties']['value']:
            ignoreKeys = schema[objname]['properties']['value']['properties'].keys()
        return ignoreKeys

    def setupCommands(self, teardown=False):
        '''
        This api will setup all the do_<command> and comlete_<command> as required by the cmdln class.
        The functionality is common for all commands so we will map the commands based on what is in
        the model.
        The function being supplied is actually a class so that we know the origional callers function
        name.
        :return:
        '''
        def isSubCmd(command):
            return 'subcmd' in command

        def isLeaf(command):
            return 'commands' in command

        def isbranch(command):
            return type(command) in (dict, jsonref.JsonRef)

        def isAttribute(command, model):
            return command in model

        def getAllSubCmdCommands(cmd, ignorkeys):
            for k, v in self.modelCmdsLoop(cmd):
                if k is None:
                    continue

                if k not in ignoreKeys:
                    if 'subcmd' in k:
                        if isbranch(v):
                            for kk, vv in v.iteritems():
                                if 'cliname' in vv:
                                    cmdname = vv['cliname']
                    else:
                        # get clicommand name from attribute
                        cmdname = self.getCliName(v)

                    if cmdname:
                        yield cmdname


        # this loop will setup each of the cliname commands for this model level
        # cmdln/cmd expects that all commands have a function associated with it
        # in the format of 'do_<command>'
        # TODO need to add support for when the cli mode does not supply the cliname
        #      in this case need to get the default from the schema model
        for model, schema in zip(self.modelList, self.schemaList):
            ignoreKeys = self.getCmdKeysToIgnore(self.objname, schema)

            for subcmds, cmd in self.modelCmdsLoop(model[self.objname]):
                if subcmds is None:
                    continue
                # handle the subcmd links links
                if isSubCmd(subcmds):
                    # sub commands typically attr and attr attributes
                    if isLeaf(cmd):
                        for cmdname in getAllSubCmdCommands(cmd, ignoreKeys):
                            if cmdname:
                                # Note needed for show
                                if '-' in cmdname:
                                    sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI\n" %(cmdname,))
                                    self.do_exit([])
                                    cmdname = cmdname.replace('-', '_')
                                #sys.stdout.write("createing do_%s\n" %(cmdname))

                                if not teardown:
                                    setattr(self.__class__, "do_" + cmdname, SetAttrFunc(self._cmd_common))
                                    setattr(self.__class__, "complete_" + cmdname, self._cmd_complete_common)
                                else:
                                    delattr(self.__class__, "do_" + cmdname)
                                    delattr(self.__class__, "complete_" + cmdname)

                    # subcmd is a ref, typically this means that this is a container leaf
                    elif isbranch(cmd):
                        # another sub command list
                        for k, v in cmd.iteritems():
                            if k not in ignoreKeys:
                                cmdname = self.getCliName(v)
                                if cmdname:
                                    #sys.stdout.write("createing do_%s\n" %(cmdname))
                                    if '-' in cmdname:
                                        sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                                        self.do_exit([])
                                        cmdname = cmdname.replace('-', '_')

                                    # Note needed for show
                                    #if cmdname != self.objname:
                                    if not teardown:
                                        setattr(self.__class__, "do_" + cmdname, SetAttrFunc(self._cmd_common))
                                        setattr(self.__class__, "complete_" + cmdname, self._cmd_complete_common)
                                    else:
                                        delattr(self.__class__, "do_" + cmdname)
                                        delattr(self.__class__, "complete_" + cmdname)

                # an attribute
                elif isAttribute(subcmds, model[self.objname]):
                    # handle commands when are not links
                    try:
                        cmdname = None
                        if 'commands' in model[self.objname][subcmds]:
                            cmdname = self.getCliName(model[self.objname][subcmds]["commands"])
                        if cmdname:
                            if '-' in cmdname:
                                sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                                self.do_exit([])
                                cmdname = cmdname.replace('-', '_')
                            if not teardown:
                                setattr(self.__class__, "do_" + cmdname, SetAttrFunc(self._cmd_common))
                            else:
                                delattr(self.__class__, "do_" + cmdname)
                    except Exception as e:
                            sys.stdout.write("EXCEPTION RAISED: %s" %(e,))

        if not teardown:
            setattr(self.__class__, "do_no", self._cmd_do_delete)
            setattr(self.__class__, "complete_no", self._cmd_complete_delete)
        else:
            delattr(self.__class__, "do_no")
            delattr(self.__class__, "complete_no")

    def modelCmdsLoop(self, model):
        if 'commands' in model:
            for cmdname, cmddata in model["commands"].iteritems():
                yield cmdname, cmddata

        yield None, None


    def teardownCommands(self):
        '''
        This api will setup all the do_<command> and comlete_<command> as required by the cmdln class.
        The functionality is common for all commands so we will map the commands based on what is in
        the model.  Once a leaf has been processed the commands need to be removed from the class otherwise
        they commands will exist under other leaf processing.
        The function being supplied is actually a class so that we know the origional callers function
        name.
        :return:
        '''
        self.setupCommands(teardown=True)

    def do_exit(self, args):
        """Exit current CLI tree position, if at base then will exit CLI"""
        self.teardownCommands()
        self.prompt = self.baseprompt
        self.stop = True

    def getObjName(self, schema):
        cmd = 'objname'
        return self.getSubCommand(cmd, schema[self.objname]["properties"]["commands"]["properties"])[0][cmd]['default']

    def prepareConfigTreeObjects(self, key, objname, createwithdefault, subcmd, model, schema, listAttrs):
        '''
        Based on the schema and model will fill in the default object parameters
        :param key:
        :param objname:
        :param subcmd:
        :param model:
        :param schema:
        :return: list of commands available from this leaf class
        '''

        def getObjNameAndCreateWithDefaultFromSchema(schema, model, objname, createwithdefault):
            objname = objname
            createwithdefault = createwithdefault
            if 'objname' in schema:
                objname = schema['objname']['default']
            if 'createwithdefault' in schema:
                createwithdefault = schema['createwithdefault']['default']
                if 'createwithdefault' in model:
                    createwithdefault = model['createwithdefault']

            return objname, createwithdefault

        cmdList = []
        cmdDict = {}
        tmpobjname = objname
        tmpcreatewithdefault = createwithdefault
        for k, v in schema.iteritems():
            if k == key:
                return v

            # TODO need to update function to ignore sub commands which are not terminating commands
            if k in model:
                tmpmodel = model[k]
                tmpobjname, tmpcreatewithdefault = getObjNameAndCreateWithDefaultFromSchema(v, tmpmodel, tmpobjname, tmpcreatewithdefault)

                # looking for subcommand attributes
                if "subcmd" in k and "commands" in v and type(v["commands"]) in (dict, jsonref.JsonRef):
                    listAttrs = v['listattrs'] if 'listattrs' in v else []
                    cmds = self.prepareConfigTreeObjects(key, tmpobjname, tmpcreatewithdefault, subcmd, tmpmodel["commands"], v["commands"]["properties"], listAttrs)
                    cmdList += cmds
                # looking for subsubcommand as this is an attribute that is an attribute,
                # this means that this is a reference to a struct or list of structs
                elif "subcmd" in k and type(v) in (dict, jsonref.JsonRef):
                    for kk, vv in tmpmodel.iteritems():
                        if kk in v:
                            subtmpschema = v[kk]['properties']
                            if 'objname' in subtmpschema:
                                tmpobjname = subtmpschema['objname']['default']

                            # a sub cmd is one which has a 'value' attribute defined
                            tmpsubcmd = None
                            if 'cliname' in vv:
                                tmpsubcmd = vv['cliname']

                            if "commands" in vv and len(vv) > 0:
                                attrDict = dict(listAttrs)
                                key = key
                                isList = False
                                if k in attrDict:
                                    key = attrDict[k]
                                    isList = True

                                # lets create the object, and tie it to the local object
                                cmds = self.prepareConfigTreeObjects(key,
                                                           tmpobjname,
                                                           tmpcreatewithdefault,
                                                           tmpsubcmd,
                                                           vv["commands"],
                                                           subtmpschema["commands"]["properties"],
                                                           listAttrs)
                                cmdList += cmds

                                # lets add the attribute to the subcmd
                                if key:
                                    cmdDict.update({tmpsubcmd : {'key': key,
                                                            'createwithdefaults' : tmpcreatewithdefault,
                                                            'subcommand' : subcmd,
                                                            'objname' :  objname,
                                                            'isattrkey': False,
                                                            'value': cmds,
                                                            'isarray': isList,
                                                            'type': tmpobjname}})

                else:
                    key = k
                    if 'subcmd' in key:
                        attrDict = dict(listAttrs)
                        key = attrDict[k]
                    cmdDict.update({tmpmodel['cliname'] : {'key': key,
                                                    'createwithdefaults' : tmpcreatewithdefault,
                                                    'subcommand' : subcmd,
                                                    'objname' : objname,
                                                    'isattrkey': v['properties']['key']['default'],
                                                    'value': v['properties']['defaultarg'],
                                                    'isarray': v['properties']['islist']['default'],
                                                    'type': v['properties']['argtype']}})

            elif 'properties' in v:
                cmdDict.update({v['properties']['cliname']['default'] : {'key': k,
                                                    'createwithdefaults' : tmpcreatewithdefault,
                                                    'subcommand' : subcmd,
                                                    'objname' : objname,
                                                    'isattrkey': v['properties']['key']['default'],
                                                    'value': v['properties']['defaultarg'],
                                                    'isarray': v['properties']['islist']['default'],
                                                    'type': v['properties']['argtype']}})

        if cmdDict:
            cmdList.append(cmdDict)

        return cmdList

    def cmdloop(self, intro=None):
        try:
            cmdln.Cmdln.cmdloop(self)
        except KeyboardInterrupt:
            self.intro = '\n'
            self.cmdloop()

    def _cmd_complete_delete(self, text, line, begidx, endidx):

        mline = [x for x in line.split(' ') if x != '']
        mline = mline[1:] if len(mline) > 1 else []

        return ['no'] + self._cmd_complete_common(text, ' '.join(mline), begidx, endidx)

    def _cmd_do_delete(self, argv):
        self._cmd_common(argv)

    def getCommandDefaultAttrValue(self, argv, delcmd=False):
        model = self.modelList[0]
        schema = self.schemaList[0]
        parentname = self.parent.lastcmd[-2]
        # should be at config x
        schemaname = self.getSchemaCommandNameFromCliName(parentname, model)
        value = None
        if schemaname:
            if len(argv) > 1:
                submodelList = self.getSubCommand(argv[0], model[schemaname]["commands"])
                subschemaList = self.getSubCommand(argv[0], schema[schemaname]["properties"]["commands"]["properties"], model[schemaname]["commands"])
                if submodelList and subschemaList:
                    schemaname = self.getSchemaCommandNameFromCliName(argv[0], submodelList[0])
                    if schemaname:
                        for i in range(1, len(argv)):
                            for submodel, subschema in zip(submodelList, subschemaList):
                                schemaname = self.getSchemaCommandNameFromCliName(argv[i-1], submodel)
                                if schemaname:
                                    submodelList = self.getSubCommand(argv[i], submodel[schemaname]["commands"])
                                    subschemaList = self.getSubCommand(argv[i], subschema[schemaname]["properties"]["commands"]["properties"], submodel[schemaname]["commands"])
                                    if submodelList and subschemaList:
                                        for subsubmodel, subsubschema in zip(submodelList, subschemaList):
                                            schemaname = self.getSchemaCommandNameFromCliName(argv[i], submodel)
                                            value = self.getModelDefaultAttrVal(argv[i], schemaname, subsubmodel, subsubschema, delcmd=delcmd)
                                    else:
                                        value = self.getModelDefaultAttrVal(argv[i], schemaname, submodel, subschema, delcmd=delcmd)
            else:
                value = self.getModelDefaultAttrVal(argv[0], schemaname, model, schema, delcmd=delcmd)


        return value

    def convertStrValueToType(self, argtype, value):

        if snapcliconst.isboolean(argtype):
            return snapcliconst.convertStrBoolToBool(value)
        elif snapcliconst.isnumeric(argtype):
            return snapcliconst.convertStrNumToNum(value)
        return value



    def _cmd_common(self, argv):
        delete = False
        mline = argv
        verifyargv = argv
        if len(argv) > 0 and argv[0] == 'no':
            verifyargv = argv[1:]
            mline = argv[1:]
            delete = True
        def isInvalidCommand(mline, delete):
            return len(mline) < 2 and not delete

        def isKeyValueCommand(mline, delete, islist):

            # command is key value
            if len(mline) == 2 and (not delete or islist):
                return True
            elif len(mline) == 2 and len(frozenset([str(mline[-1]).lower()]).intersection(
                snapcliconst.CLI_COMMAND_POSITIVE_TRUTH_VALUES + snapcliconst.CLI_COMMAND_NEGATIVE_TRUTH_VALUES)) == 1:
                return True
            # command is a delete command which does not require a value
            elif len(mline) == 1 and delete:
                return True

            return False

        # lets fill in a default value if one is not supplied.  This is only
        # valid for boolean attributes and attributes which only contain two
        # enum types
        value = self.getCommandDefaultAttrValue(mline, delcmd=delete)
        if value is not None:
            mline += [str(value)]
        if isInvalidCommand(verifyargv, delete):
            return
        elif isKeyValueCommand(verifyargv, delete, self.issubcommandlist):
            # key value supplied
            self.processKeyValueCommand(mline, delete)
        else:
            self.processSubKeyKeyValueCommand(mline, delete)

        if self.subcommand:
            # reset the command len
            self.commandLen = 0

            model = self.modelList[0]
            schema = self.schemaList[0]

            endprompt = self.baseprompt[-2:]

            parentname = self.parent.lastcmd[-2]
            # should be at config x
            schemaname = self.getSchemaCommandNameFromCliName(parentname, model)
            if schemaname:
                submodelList = self.getSubCommand(argv[0], model[schemaname]["commands"])
                subschemaList = self.getSubCommand(argv[0], schema[schemaname]["properties"]["commands"]["properties"], model[schemaname]["commands"])
                if submodelList and subschemaList:

                    schemaname = self.getSchemaCommandNameFromCliName(argv[0], submodelList[0])
                    if schemaname:
                        value = None
                        if snapcliconst.COMMAND_TYPE_DELETE not in self.cmdtype:
                            self.prompt = self.baseprompt[:-2] + '-'

                            configprompt = self.getPrompt(submodelList[0][schemaname], subschemaList[0][schemaname])
                            if configprompt:
                                self.prompt += configprompt + '-'
                                value = argv[-1]

                        objname = schemaname
                        for i in range(1, len(argv)-1):
                            for submodel, subschema in zip(submodelList, subschemaList):
                                schemaname = self.getSchemaCommandNameFromCliName(argv[i-1], submodel)
                                if schemaname:
                                    submodelList = self.getSubCommand(argv[i], submodel[schemaname]["commands"])
                                    subschemaList = self.getSubCommand(argv[i], subschema[schemaname]["properties"]["commands"]["properties"], submodel[schemaname]["commands"])
                                    for submodel, subschema in zip(submodelList, subschemaList):
                                        schemaname = self.getSchemaCommandNameFromCliName(argv[i], submodel)
                                        if schemaname:
                                            configprompt = self.getPrompt(submodel[schemaname], subschema[schemaname])
                                            objname = schemaname
                                            if configprompt and snapcliconst.COMMAND_TYPE_DELETE not in self.cmdtype:
                                                self.prompt += configprompt + '-'
                                                value = argv[-1]

                        if value != None:
                            self.prompt += value + endprompt
                        elif snapcliconst.COMMAND_TYPE_DELETE not in self.cmdtype:
                            self.prompt = self.prompt[:-1] + endprompt
                        self.stop = True
                        prevcmd = self.currentcmd
                        self.currentcmd = self.lastcmd
                        # stop the command loop for config as we will be running a new cmd loop
                        cmdln.Cmdln.stop = True
                        self.teardownCommands()
                        c = LeafCmd(objname, argv[-2], self.cmdtype, self.parent, self.prompt, submodelList, subschemaList)
                        c.currentcmd = self.lastcmd
                        if c.applybaseconfig(argv[-2]):
                            c.cmdloop()
                        self.setupCommands()
                        if snapcliconst.COMMAND_TYPE_DELETE in self.cmdtype:
                            self.cmdtype = snapcliconst.COMMAND_TYPE_CONFIG

                        self.subcommand = False
                        self.prompt = self.baseprompt
                        self.currentcmd = prevcmd

        # lets restart the cmdloop
        if self.stop:
            self.cmdloop()

    def processSubKeyKeyValueCommand(self, mline, delete):
        """
        This is mean to handle commands which contain a
        subcommand + attr + value
        :param mline:
        :param delete:
        :return:
        """
        def isSubCommandAttrOrSubLeaf(config, key, subkey, issubcommand):
            """
            v['subcommand'] is a the containing leaf

            :param config: configuration object
            :param key:
            :param subkey: typically an attribute of a leaf container or a key of a
                           of a leaf container

            :param issubcommand: this is a terminating command meaning the subkey
                                 is a key of a leaf container
            :return:
            """
            return len([k for k, v in config.keysDict.iteritems() if ((v['subcommand'] == key
                                                                       and not issubcommand
                                                                       and k == subkey) or
                                                                          (issubcommand and
                                                                                   k == subkey))]) == 1

        # key + subkey + value supplied
        key = mline[0]
        subkey = mline[1]
        value = mline[2] if not delete else None
        configObj = self.getConfigObj()
        if configObj:
            for config in configObj.configList:
                if isSubCommandAttrOrSubLeaf(config, key, subkey, self.subcommand):
                    # need to be smarter about when attributes are set so lets check the parent
                    # to see this config is my key if it is not then move on
                    foundConfig = True
                    if self.parent:
                        parentKey = self.parent.lastcmd[-2]
                        parentValue = self.parent.lastcmd[-1]
                        foundConfig = False
                        for entry in config.attrList:
                            if entry.isKey() and \
                                parentKey == entry.attr and \
                                    parentValue == entry.val:
                                foundConfig = True

                    # lets update only if this is not a subcommand
                    # otherwise this will be updated as part of
                    # subcommand processing
                    if foundConfig and ((not self.subcommand and not delete) or (delete)):
                        # delete shoudl only be set if a key is being deleted
                        if delete and value is None:
                            config.setDelete(True)

                        if len(config.attrList) > 1 and delete:
                            config.clear(subkey, value)
                            config.setValid(False)
                        else:
                            config.set(self.lastcmd, delete, subkey, value)
                            config.setValid(True)

    def processKeyValueCommand(self, mline, delete):
        key = self.parentcliname if not self.subcommand else None
        subkey = mline[0]
        value = mline[1] if len(mline) == 2 else None
        configObj = self.getConfigObj()
        if configObj:
            # TODO need to handle if config has been applied then another attribute set
            for config in configObj.configList:
                for k, v in config.keysDict.iteritems():
                    # is key part of the subcommand
                    # is subkey == attr k
                    # or is subkey in the sub-attributes (struct)
                    # or attr is a key for another attribute
                    if ((key in (v['subcommand'], None)) and
                                k == subkey and
                            (type(v['value']) is not list)):

                        foundConfig = True
                        if self.parent:
                            if len(self.currentcmd) == 0:
                                parentKey = self.parent.lastcmd[-2] if len(self.parent.lastcmd) > 1 else \
                                self.parent.lastcmd[-1]
                                parentValue = self.parent.lastcmd[-1] if len(self.parent.lastcmd) > 0 else None
                            else:
                                parentKey = self.currentcmd[-2] if len(self.currentcmd) > 1 else self.currentcmd[-1]
                                parentValue = self.currentcmd[-1] if len(self.currentcmd) > 0 else None
                            foundConfig = False
                            for entry in config.attrList:
                                if entry.isKey() and \
                                    parentKey == entry.attr and \
                                        parentValue == entry.val:
                                    foundConfig = True

                        # lets update only if this is not a subcommand
                        # otherwise this will be updated as part of
                        # subcommand processing
                        if foundConfig and ((not self.subcommand and not delete) or (delete)):
                            # delete should only be set is a key is being deleted
                            # or if there is not a default to revert to
                            if delete and value is None:
                                config.setDelete(True)

                            if config.isAttrSet(subkey) and delete:
                                config.clear(subkey, value)
                                isvalid = v['createwithdefaults']
                                config.setValid(isvalid)
                            else:
                                # store the attribute into the config
                                config.set(self.lastcmd, delete, subkey, value, isKey=self.subcommand,
                                           isattrlist=v['isarray'])
                                config.setValid(True)


                    # when we fill in the config we set a value to be a placeholder for the sub list attributes
                    # thus we want to check to see if the subkey from the command exists within the list attribute
                    # keys
                    elif (type(v['value']) is list and \
                                  len(v['value']) and subkey in v['value'][0].keys()):

                        def isKeyInSubListAttr(parentKey, parentValue, entryval):
                            # the values are converted when stored cause I am not storing the subattr types
                            # so lets convert the value back to a string to compare against
                            return len(
                                [x for x in entryval if parentKey in x and str(x[parentKey]) == parentValue]) == 1

                        foundConfig = True
                        parentKey = None
                        parentValue = None
                        if self.parent:
                            if len(self.currentcmd) == 0:
                                parentKey = self.parent.lastcmd[-2] if len(self.parent.lastcmd) > 1 else \
                                self.parent.lastcmd[-1]
                                parentValue = self.parent.lastcmd[-1] if len(self.parent.lastcmd) > 0 else None
                            else:
                                parentKey = self.currentcmd[-2] if len(self.currentcmd) > 1 else self.currentcmd[-1]
                                parentValue = self.currentcmd[-1] if len(self.currentcmd) > 0 else None
                            foundConfig = False
                            for entry in config.attrList:
                                if entry.isKey() and \
                                                parentKey == entry.attr and \
                                        (parentValue == entry.val or
                                                     type(entry.val) is list and isKeyInSubListAttr(parentKey,
                                                                                                    parentValue,
                                                                                                    entry.val)):
                                    foundConfig = True

                        if foundConfig:
                            # lets set the
                            if config.isAttrSet(subkey) and delete:
                                config.clear(subkey, value)
                                # cleared an attribute and defaults not set
                                isvalid = v['createwithdefaults']
                                config.clear(isvalid)
                            else:
                                # TODO this will need to be updated once we allow for multiple attributes
                                # to be set at the same time.
                                if parentKey in [vv['subcommand'] for vv in v['value'][0].values()]:
                                    # change the subkey to be the list key so that we don't create a new attr update
                                    attrkey = parentKey
                                    data = {}
                                    # the values are converted cause I am not storing the subattr types
                                    for kk, vv in v['value'][0].iteritems():
                                        if kk != subkey:
                                            data.update({parentKey: self.convertStrValueToType(vv['type']['type'],
                                                                                               parentValue)})
                                        else:
                                            data.update({subkey: self.convertStrValueToType(vv['type']['type'], value)})
                                else:
                                    attrkey = subkey
                                    data = {}
                                    # the values are converted cause I am not storing the subattr types
                                    for kk, vv in v['value'][0].iteritems():
                                        if kk == subkey:
                                            data.update({subkey: self.convertStrValueToType(vv['type']['type'], value)})
                                        else:
                                            data.update({kk: self.convertStrValueToType(vv['type']['type'],
                                                                                        vv['value']['default'])})

                                # store the attribute into the config
                                config.setDict(self.lastcmd, delete, attrkey, data, isKey=self.subcommand,
                                               isattrlist=v['isarray'])

    def complete_redistribute(self, text, line, begidx, endidx):
        return self._cmd_complete_common(text, line, begidx, endidx)

    # this complete is meant for sub ethernet commands
    # for example:
    # >ip address 10.1.1.1
    def _cmd_complete_common(self, text, line, begidx, endidx):
        #sys.stdout.write("\nline: %s text: %s %s\n" %(line, text, not text))
        # remove spacing/tab
        parentcmd = self.parent.lastcmd[-2] if len(self.parent.lastcmd) > 1 else self.parent.lastcmd[-1]
        mline = [parentcmd] + [x for x in line.split(' ') if x != '']
        mlineLength = len(mline)
        #sys.stdout.write("\nmline: %s\n" %(mline))

        subcommands = []
        # no comamnd case
        if len(mline) == 1:
            for f in dir(self.__class__):
                if f.startswith('do_') and not f.endswith('no'):
                    subcommands.append(f.lstrip('do_'))

        submodel = self.modelList[0]
        subschema = self.schemaList[0]
        skipValue = False
        for i in range(1, mlineLength):
            if skipValue:
                skipValue = False
                continue

            schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], submodel)
            if schemaname:
                submodelList, subschemaList = self.getSubCommand(mline[i], submodel[schemaname]["commands"]), \
                                                self.getSubCommand(mline[i],
                                                                   subschema[schemaname]["properties"]["commands"]["properties"],
                                                                   submodel[schemaname]["commands"])
                if submodelList and subschemaList:
                    for submodel, subschema in zip(submodelList, subschemaList):
                        (valueexpected, objname, keys, help, islist) = self.isValueExpected(mline[i], submodel, subschema)
                        if valueexpected != SUBCOMMAND_VALUE_NOT_EXPECTED:

                            if valueexpected == SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE:
                                config = self.getConfigObj()
                                values = self.getValueSelections(mline[i], submodel, subschema)
                                if not values:
                                    values = config.getCommandValues(objname, keys)
                                #sys.stdout.write("\nvalue expected: mline %s i %s mlinelength %s values %s\n" %(mline, i, mlineLength, values))
                                # expect value but no value supplied
                                if (i == mlineLength-1):
                                    #sys.stdout.write("\nselections: %s\n" %(values))
                                    subcommands = values
                                # expect value and something supplied
                                elif (i == mlineLength-2 and mline[i+1] not in values):
                                    subcommands = values
                                    skipValue = True
                        else:
                            subcommands = self.getchildrencmds(mline[i], submodel, subschema, issubcmd=True)
                            subcommands = [x for x in subcommands if x[0] != mline[0]]
                else:
                    def checkAttributevalues(mline, i, mlineLength, schemaname, submodel, subschema):

                        subcommands = []
                        for mcmd, mcmdvalues in submodel[schemaname]['commands'].iteritems():
                            scmdvalues = subschema[schemaname]['properties']['commands']['properties'][mcmd]
                            if 'subcmd' in mcmd:
                                if self.isCommandLeafAttrs(mcmdvalues, scmdvalues):
                                    if i == (mlineLength - 1): # value expected from attrs
                                        # reached attribute values
                                        for attr, attrvalue in mcmdvalues['commands'].iteritems():
                                            sattrvalue = scmdvalues['commands']['properties'][attr]
                                            if 'cliname' in attrvalue:
                                                if attrvalue['cliname'] == mline[i]:
                                                    subcommands.append([snapcliconst.getAttrCliName(attrvalue, sattrvalue),
                                                                   snapcliconst.getAttrHelp(attrvalue, sattrvalue)])
                                            else:
                                                for subkey in attrvalue.keys():
                                                    subcommands += checkAttributevalues(mline, i, mlineLength, subkey, attrvalue, sattrvalue)
                        return subcommands

                    subcommands += checkAttributevalues(mline, i, mlineLength, schemaname, submodel, subschema)

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

    def xdo_show(self, argv):
        root = self.getRootObj()
        if root:
            if hasattr(root, '_cmd_show'):
                root._cmd_show(argv)

    def display_help(self, argv):

        def checkAttributevalues(argv, mlineLength, schemaname, submodel, subschema):
            subcommands = []
            for mcmd, mcmdvalues in submodel[schemaname]['commands'].iteritems():
                scmdvalues = subschema[schemaname]['properties']['commands']['properties'][mcmd]
                if 'subcmd' in mcmd:
                    if self.isCommandLeafAttrs(mcmdvalues, scmdvalues):
                        if i == (mlineLength - 1): # value expected from attrs
                            # reached attribute values
                            for attr, attrvalue in mcmdvalues['commands'].iteritems():
                                sattrvalue = scmdvalues['commands']['properties'][attr]
                                if 'cliname' in attrvalue:
                                    if attrvalue['cliname'] == mline[i]:
                                        subcommands.append([snapcliconst.getAttrCliName(attrvalue, sattrvalue),
                                                       snapcliconst.getAttrHelp(attrvalue, sattrvalue)])
                                else:
                                    for subkey in attrvalue.keys():
                                        subcommands += checkAttributevalues(argv, mlineLength, subkey, attrvalue, sattrvalue)
            subcommands = [x for x in subcommands if x[0] not in argv or ('?' in argv or 'help' in argv)]
            return subcommands

        # sub commands within a config command will have the current cmd set
        if len(self.currentcmd) == 0:
            parentcmd = self.parent.lastcmd[-2] if len(self.parent.lastcmd) > 1 else self.parent.lastcmd[-1]
        else:
            parentcmd = self.currentcmd[-2] if len(self.currentcmd) > 1 else self.currentcmd[-1]
        mline = [parentcmd] + argv[:-1]
        mlineLength = len(mline)

        subcommands = [["<cr>", ""]]
        if mlineLength == 1:
            for model, schema in zip(self.modelList, self.schemaList):
                subcommands = self.getchildrenhelpcmds(mline[0], model, schema)
                # exclude parent command
                if len(self.currentcmd) > 0:
                    parentcmd = self.parent.lastcmd[-2] if len(self.parent.lastcmd) > 1 else self.parent.lastcmd[-1]
                    subcommands = [x for x in subcommands if x[0] != parentcmd]

        #ignore the help or ? command
        submodel = self.modelList[0]
        subschema = self.schemaList[0]
        for i in range(1, mlineLength):
            schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], submodel)
            if schemaname:
                submodelList, subschemaList = self.getSubCommand(mline[i], submodel[schemaname]["commands"]), \
                                              self.getSubCommand(mline[i], subschema[schemaname]["properties"]["commands"]["properties"],
                                                                 submodel[schemaname]["commands"])
                if submodelList and subschemaList:
                    for submodel, subschema in zip(submodelList, subschemaList):
                        (valueexpected, objname, keys, help, islist) = self.isValueExpected(mline[i], submodel, subschema)
                        if i == mlineLength - 1:
                            if valueexpected != SUBCOMMAND_VALUE_NOT_EXPECTED:
                                cmd = " ".join(argv[:-1])
                                subcommands = [[cmd, help]]
                            else:
                                subcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema, issubcmd=True)
                                subcommands = [x for x in subcommands if x[0] != mline[0]]
                        #else:
                        #    subcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema)
                        #    subcommands = [x for x in subcommands if x[0] != mline[0]]

                else:
                    subcommands = checkAttributevalues(argv, mlineLength, schemaname, submodel, subschema)

        self.printCommands(mline, subcommands)

    def do_help(self, argv):
        self.display_help(argv)

    def precmd(self, argv):
        self.issubcommandlist = False
        parentcmd = self.parent.lastcmd[-2] if len(self.parent.lastcmd) > 1 else self.parent.lastcmd[-1]
        delete = argv[0] == 'no' if argv else False
        mline = [parentcmd] + [x for x in argv if x != 'no']
        mlineLength = len(mline)
        subschema = self.schemaList[0] if self.schemaList else None
        submodel = self.modelList[0] if self.modelList else None
        cmd = argv[-1] if argv else ''
        if cmd in ('?', ) and cmd not in ('exit', 'end', 'help', 'no', '!'):
            self.display_help(argv if argv[0] != 'no' else argv[1:])
            return ''
        if cmd in ('!', ):
            self.do_exit(argv if argv[0] != 'no' else argv[1:])
            return ''

        if subschema and submodel:
            if mlineLength > 0:
                self.commandLen = 0
                for i in range(1, mlineLength):
                    schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], submodel)
                    if schemaname in subschema and schemaname in submodel:
                        subschemaList, submodelList = self.getSubCommand(mline[i],
                                                                         subschema[schemaname]["properties"]["commands"]["properties"],
                                                                         submodel[schemaname]["commands"]), \
                                                        self.getSubCommand(mline[i], submodel[schemaname]["commands"])
                        issubcommandalist = self.isSubCommandList(mline[i],
                                                                 subschema[schemaname]["properties"]["commands"]["properties"],
                                                                 submodel[schemaname]["commands"])

                        if subschemaList and submodelList:
                            for submodel, subschema in zip(submodelList, subschemaList):
                                (valueexpected, objname, keys, help, islist) = self.isValueExpected(mline[i], submodel, subschema)
                                if valueexpected != SUBCOMMAND_VALUE_NOT_EXPECTED:
                                    if not delete:
                                        values = self.getValueSelections(mline[i], submodel, subschema)
                                        strvalues = []
                                        if values:
                                            strvalues = ["%s" %(x,) for x in values]
                                        if i < mlineLength and values and mline[i+1] not in strvalues:
                                            snapcliconst.printErrorValueCmd(i, mline)
                                            sys.stdout.write("\nERROR: Invalid Selection %s, must be one of %s\n" % (mline[i+1], ",".join(strvalues)))
                                            return ''
                                        min,max = self.getValueMinMax(mline[i], submodel, subschema)
                                        if min is not None and max is not None:
                                            try:
                                                if i < mlineLength - 1:
                                                    num = string.atoi(mline[i+1])
                                                    if num < min or num > max:
                                                        snapcliconst.printErrorValueCmd(i, mline)
                                                        sys.stdout.write("\nERROR: Invalid Value %s, must be beteween %s-%s\n" % (mline[i+1], min, max))
                                                        return ''
                                                else:
                                                    sys.stdout.write("\nERROR: Value Expected, must be beteween %s-%s\n" % (min, max))
                                                    return ''

                                            except:
                                                sys.stdout.write("\nERROR: Invalid Value %s, must be beteween %s-%s\n" % (mline[i+1], min, max))
                                                return ''

                                        if valueexpected == SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE and \
                                            i == mlineLength - 1:
                                            sys.stdout.write("\nERROR: Value expected")
                                    elif i == mlineLength - 2 and not islist and not issubcommandalist:
                                        erroridx = i+1 if not delete else i+2
                                        errcmd = mline if not delete else ['no'] + mline
                                        snapcliconst.printErrorValueCmd(erroridx, errcmd)
                                        sys.stdout.write("\nERROR Delete commands do not expect value, will revert to default if exists\n")
                                    # found that if commands are entered after the last command then there can be a problem
                                    self.commandLen = len(mline[:i]) + 1
                                    self.subcommand = True
                                    self.issubcommandlist = issubcommandalist
                                else:
                                    self.commandLen = len(mline[:i])

                        else:

                            def checkAttributevalues(argv, mlineLength, schemaname, submodel, subschema, delete):

                                for mcmd, mcmdvalues in submodel[schemaname]['commands'].iteritems():
                                    scmdvalues = subschema[schemaname]['properties']['commands']['properties'][mcmd]
                                    if 'subcmd' in mcmd:
                                        if self.isCommandLeafAttrs(mcmdvalues, scmdvalues):
                                            if not delete and i == (mlineLength - 2):  # value expected from attrs
                                                # reached attribute values
                                                for attr, attrvalue in mcmdvalues['commands'].iteritems():
                                                    sattrvalue = scmdvalues['commands']['properties'][attr]
                                                    if 'cliname' in attrvalue:
                                                        if attrvalue['cliname'] == mline[i]:
                                                            self.subcommand = False
                                                            values = snapcliconst.getSchemaAttrSelection(sattrvalue)
                                                            if values:
                                                                strvalues = ["%s" %(x,) for x in values]
                                                            if values and mline[i+1] not in strvalues:
                                                                snapcliconst.printErrorValueCmd(i, mline)
                                                                sys.stdout.write("\nERROR: Invalid Selection %s, must be one of %s\n" % (mline[i+1], ",".join(strvalues)))
                                                                return ''
                                                            min,max = snapcliconst.getSchemaAttrMinMax(sattrvalue)
                                                            if min is not None and max is not None:
                                                                try:
                                                                    num = string.atoi(mline[i+1])
                                                                    if num < min or num > max:
                                                                        snapcliconst.printErrorValueCmd(i, mline)
                                                                        sys.stdout.write("\nERROR: Invalid Value %s, must be beteween %s-%s\n" % (mline[i+1], min, max))
                                                                        return ''
                                                                except:
                                                                    sys.stdout.write("\nERROR: Invalid Value %s, must be beteween %s-%s\n" % (mline[i+1], min, max))
                                                                    return ''
                                                    else:
                                                        self.subcommand = True
                                                        self.issubcommandlist = False
                                                        for subkey in attrvalue.keys():
                                                            checkAttributevalues(argv, mlineLength, subkey, attrvalue, sattrvalue, delete)
                                            elif delete and i == (mlineLength - 2):
                                                erroridx = i+1 if not delete else i+2
                                                errcmd = mline if not delete else ['no'] + mline
                                                snapcliconst.printErrorValueCmd(erroridx, errcmd)
                                                sys.stdout.write("\nERROR Delete commands do not expect value, will revert to default if exists\n")
                                                return ''


                                return argv

                            return checkAttributevalues(argv, mlineLength, schemaname, submodel, subschema, delete)

        return argv
