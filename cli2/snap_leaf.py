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
# This is a leaf node which should handle command attributes related to a leaf model
#
import sys
import cmdln
import json
import jsonref
import string
from sets import Set
from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine, SUBCOMMAND_VALUE_NOT_EXPECTED, \
    SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE, SUBCOMMAND_VALUE_EXPECTED
from cmdEntry import CmdEntry, isboolean, isnumeric
from const import *

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
        self.subcommand = False


        self.setupCommands()

    def applybaseconfig(self, cliname):
        '''
        Function is called to apply the command used when creating this class.
        Basically this should mean that a KEY for a given object / command is being
        created.
        :param cliname:
        :return:
        '''
        configObj = self.getConfigObj()
        for model, schema in zip(self.modelList, self.schemaList):

            listAttrs =  model[self.objname]['listattrs'] if 'listattrs' in model[self.objname] else []
            # lets get all commands and subcommands for a given config operation
            allCmdsList = self.prepareConfigTreeObjects(None, self.objname, False, model[self.objname]['cliname'], model[self.objname]["commands"], schema[self.objname]["properties"]["commands"]["properties"], listAttrs)
            objDict = {}

            # lets fill out the object to attributes mapping valid for this level in the tree
            for cmds in allCmdsList:
                for k, v in cmds.iteritems():
                    if v['objname'] not in objDict:
                        objDict[v['objname']] = {}

                    objDict[v['objname']].update({k:v})


            if configObj:
                # lets go through the valid sub tree commands
                # and fill in what commands were entered by the user
                for k, v in objDict.iteritems():
                    config = CmdEntry(k, objDict[k])
                    if COMMAND_TYPE_SHOW not in self.cmdtype:
                        lastcmd = self.parent.lastcmd[-2] if COMMAND_TYPE_CONFIG_NOW not in self.cmdtype else self.parent.lastcmd[-1]
                        if cliname == lastcmd:
                            for kk in v.keys():
                                if kk == cliname:
                                    basekey = self.parent.lastcmd[-2]  if COMMAND_TYPE_CONFIG_NOW not in self.cmdtype else self.parent.lastcmd[-1]
                                    basevalue = self.parent.lastcmd[-1]  if COMMAND_TYPE_CONFIG_NOW not in self.cmdtype else None

                                    delete = True if COMMAND_TYPE_DELETE in self.cmdtype else False

                                    if basevalue is None:
                                        basevalue = self.getCommandDefaultAttrValue([basekey], delcmd=delete)

                                    # letting me know that the parent config can
                                    # create a default object, otherwise engine will
                                    # try to create a lot of objects
                                    config.setValid(v[basekey]['createwithdefaults'])

                                    config.set(self.parent.lastcmd, delete, basekey, basevalue, isKey=True)
                    else:
                        config.setValid(True)

                    # only add this config if it does not already exist
                    cfg = configObj.doesConfigExist(config)
                    if not cfg:
                        configObj.configList.append(config)
                    elif cfg and COMMAND_TYPE_DELETE in self.cmdtype:
                        # let remove the previous command if it was set
                        # or lets delete the config
                        if len(config.attrList) > 1:
                            config.clear(basekey, basevalue)
                        else:
                            try:
                                # lets remove this command
                                # because basically the user cleared
                                # the previous unapplied command
                                configObj.configList.remove(cfg)
                                return False
                            except ValueError:
                                pass
        return True if COMMAND_TYPE_CONFIG_NOW not in self.cmdtype else False

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

                        subtmpschema = v[kk]['properties']
                        if 'objname' in subtmpschema:
                            tmpobjname = subtmpschema['objname']['default']

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
                            cmdDict.update({tmpsubcmd : {'key': key,
                                                    'createwithdefaults' : tmpcreatewithdefault,
                                                    'subcommand' : subcmd,
                                                    'objname' :  objname,
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
                                                    'value': v['properties']['defaultarg'],
                                                    'isarray': v['properties']['islist']['default'],
                                                    'type': v['properties']['argtype']}})
            elif 'properties' in v:
                cmdDict.update({v['properties']['cliname']['default'] : {'key': k,
                                                    'createwithdefaults' : tmpcreatewithdefault,
                                                    'subcommand' : subcmd,
                                                    'objname' : objname,
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

        return self._cmd_complete_common(text, ' '.join(mline), begidx, endidx)

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
                                    for subsubmodel, subsubschema in zip(submodelList, subschemaList):
                                        value = self.getModelDefaultAttrVal(argv, schemaname, subsubmodel, subsubschema, delcmd=delcmd)
            else:
                value = self.getModelDefaultAttrVal(argv, schemaname, model, schema, delcmd=delcmd)


        return value

    def _cmd_common(self, argv):
        delete = False
        mline = argv
        if len(argv) > 0 and argv[0] == 'no':
            mline = argv[1:]
            delete = True

        # lets fill in a default value if one is not supplied.  This is only
        # valid for boolean attributes and attributes which only contain two
        # enum types
        value = self.getCommandDefaultAttrValue(mline, delcmd=delete)
        if value is not None:
            mline += [value]

        if len(mline) < 2:
            return
        elif len(mline) == 2:
            # key value supplied
            key = self.parentcliname if not self.subcommand else None
            subkey = mline[0]
            value = mline[1]

            configObj = self.getConfigObj()
            if configObj:
                # TODO need to handle if config has been applied then another attribute set
                for config in configObj.configList:
                    for k, v in config.keysDict.iteritems():
                        # is key part of the subcommand
                        # is subkey == attr k
                        # or is subkey in the sub-attributes (struct)
                        if ((key in (v['subcommand'], None)) and
                            k == subkey and
                                (type(v['value']) is not list)):
                            config.setValid(True)
                            if config.isAttrSet(subkey) and delete:
                                config.clear(subkey, value)
                            else:
                                # store the attribute into the config
                                config.set(self.lastcmd, delete, subkey, value, isattrlist=v['isarray'])
                        elif (type(v['value']) is list and len(v['value']) and subkey in v['value'][0].keys()):
                            # lets set the
                            if config.isAttrSet(subkey) and delete:
                                config.clear(subkey, value)
                            else:
                                # TODO this will need to be updated once we allow for multiple attributes
                                # to be set at the same time.
                                if self.parent.lastcmd[-2] not in [vv['subcommand'] for vv in v['value'][0].values()]:
                                    # change the subkey to be the list key so that we don't create a new attr update
                                    attrkey = self.parent.lastcmd[-2]
                                    data = {self.parent.lastcmd[-2]: self.parent.lastcmd[-1],
                                            subkey: value}
                                else:
                                    attrkey = subkey
                                    data = {subkey: value}
                                    for kk, vv in v['value'][0].iteritems():
                                        if kk != subkey:
                                            data.update({kk: vv['value']['default']})

                                # store the attribute into the config
                                config.setDict(self.lastcmd, delete, attrkey, data, isattrlist=v['isarray'])
        else:
            # key + subkey + value supplied
            key = mline[0]
            subkey = mline[1]
            value = mline[2]
            configObj = self.getConfigObj()
            if configObj:
                for config in configObj.configList:
                    if len([x for x,v in config.keysDict.iteritems() if v['subcommand'] == key and x == subkey]) == 1:
                        config.setValid(True)
                        if len(config.attrList) > 1 and delete:
                            config.clear(subkey, value)
                        else:
                            config.set(self.lastcmd, delete, subkey, value)

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
                        configprompt = self.getPrompt(submodelList[0][schemaname], subschemaList[0][schemaname])
                        if COMMAND_TYPE_DELETE not in self.cmdtype:
                            self.prompt = self.baseprompt[:-2] + '-' + configprompt + '-'

                        value = None
                        if configprompt and len(argv) == 2:
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
                                            if configprompt and COMMAND_TYPE_DELETE not in sel.cmdtype:
                                                self.prompt += configprompt + '-'
                                                value = argv[-1]

                        if value != None:
                            self.prompt += value + endprompt
                        elif COMMAND_TYPE_DELETE not in self.cmdtype:
                            self.prompt = self.prompt[:-1] + endprompt
                        self.stop = True
                        prevcmd = self.currentcmd
                        self.currentcmd = self.lastcmd
                        # stop the command loop for config as we will be running a new cmd loop
                        cmdln.Cmdln.stop = True
                        self.teardownCommands()
                        c = LeafCmd(objname, argv[-2], self.cmdtype, self, self.prompt, submodelList, subschemaList)
                        if c.applybaseconfig(argv[-2]):
                            c.cmdloop()
                        self.setupCommands()
                        if COMMAND_TYPE_DELETE in self.cmdtype:
                            self.cmdtype = COMMAND_TYPE_CONFIG

                        self.subcommand = False
                        self.prompt = self.baseprompt
                        self.currentcmd = prevcmd

        # lets restart the cmdloop
        if self.stop:
            self.cmdloop()

    def getchildrencmds(self, parentname, model, schema):
        attrlist = []
        if model:
            schemaname = self.getSchemaCommandNameFromCliName(parentname, model)
            if schemaname in model:
                for cmdobj in [obj for k, obj in model[schemaname]["commands"].iteritems() if "subcmd" in k]:
                    if type(cmdobj) in (dict, jsonref.JsonRef):
                        for v in cmdobj["commands"].values():
                            if 'cliname' in v and v['cliname'] != self.objname:
                                attrlist.append(v['cliname'])
        return attrlist

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

        skipValue = False
        for i in range(1, mlineLength):
            if skipValue:
                #sys.stdout.write("\nvalue expected: i %s mlinelength %s\n" %(i, mlineLength))
                skipValue = False
                continue

            #sys.stdout.write("complete: mline[%s]=%s\n" %(i, mline[i]))
            for model, schema in zip(self.modelList, self.schemaList):
                #sys.stdout.write("model %s\n schema %s\n mline[%s] %s\n" %(model, schema, i, mline[i]))
                schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], model)
                #sys.stdout.write("schemaname: %s\n" %(schemaname))
                if schemaname:
                    #sys.stdout.write("\nschemaname %s\n\n" %(schemaname))
                    submodelList, subschemaList = self.getSubCommand(mline[i], model[schemaname]["commands"]), \
                                                    self.getSubCommand(mline[i], schema[schemaname]["properties"]["commands"]["properties"], model[schemaname]["commands"])
                    #sys.stdout.write("submoduleList %s\nsubschemaList %s\n" %(submodelList, subschemaList))
                    if submodelList and subschemaList:
                        for submodel, subschema in zip(submodelList, subschemaList):
                            #sys.stdout.write("submodel %s\n subschema %s\n mline %s" %(submodel, subschema, mline[i]))
                            (valueexpected, objname, keys, help) = self.isValueExpected(mline[i], submodel, subschema)
                            #sys.stdout.write("\ncomplete:  10 value expected %s command %s\n" %(valueexpected, mline[i]))
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
                                subcommands += self.getchildrencmds(mline[i], submodel, subschema)
                            #sys.stdout.write("subcommands %s" %(subcommands,))
                    else:
                        sys.logger.write("model commands: %s\n" %(model[schemaname]["commands"]))

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

    def show_state(self, all=False):
        configObj = self.getConfigObj()
        if configObj:
            configObj.show_state(all)

    def display_help(self, argv):
        parentcmd = self.parent.lastcmd[-2] if len(self.parent.lastcmd) > 1 else self.parent.lastcmd[-1]
        mline = [parentcmd] + argv[:-1]
        mlineLength = len(mline)

        subcommands = []
        if mlineLength == 1:
            for model, schema in zip(self.modelList, self.schemaList):
                subcommands = self.getchildrenhelpcmds(mline[0], model, schema)

        #ignore the help or ? command
        for i in range(1, mlineLength):
            for model, schema in zip(self.modelList, self.schemaList):
                schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], model)
                if schemaname:
                    submodelList, subschemaList = self.getSubCommand(mline[i], model[schemaname]["commands"]), \
                                                  self.getSubCommand(mline[i], schema[schemaname]["properties"]["commands"]["properties"],
                                                                     model[schemaname]["commands"])
                    if submodelList and subschemaList:
                        for submodel, subschema in zip(submodelList, subschemaList):
                            (valueexpected, objname, keys, help) = self.isValueExpected(mline[i], submodel, subschema)
                            if i == mlineLength - 1:
                                if valueexpected != SUBCOMMAND_VALUE_NOT_EXPECTED:
                                    cmd = " ".join(argv[:-1])
                                    subcommands = [[cmd, help]]
                                else:
                                    subcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema)

        self.printCommands(mline, subcommands)

    def do_help(self, argv):
        self.display_help(argv)

    def precmd(self, argv):

        mlineLength = len(argv) - (1 if 'no' in argv else 0)
        parentcmd = self.parent.lastcmd[-2] if len(self.parent.lastcmd) > 1 else self.parent.lastcmd[-1]
        mline = [parentcmd] + [x for x in argv if x != 'no']
        subschema = self.schemaList[0] if self.schemaList else None
        submodel = self.modelList[0] if self.modelList else None

        if subschema and submodel:
            if mlineLength > 0:
                self.commandLen = 0
                for i in range(1, mlineLength):
                    schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], submodel)
                    if schemaname:
                        subschemaList, submodelList = self.getSubCommand(mline[i],
                                                                         subschema[schemaname]["properties"]["commands"]["properties"],
                                                                         submodel[schemaname]["commands"]), \
                                                        self.getSubCommand(mline[i], submodel[schemaname]["commands"])
                        if subschemaList and submodelList:
                            for submodel, subschema in zip(submodelList, subschemaList):
                                (valueexpected, objname, keys, help) = self.isValueExpected(mline[i], submodel, subschema)
                                if i == (mlineLength - 1):
                                    if valueexpected != SUBCOMMAND_VALUE_NOT_EXPECTED:
                                        #if mlineLength - i > 1:
                                        #    sys.stdout.write("Invalid command entered, ignoring\n")
                                        #    return ''

                                        values = self.getValueSelections(mline[i], submodel, subschema)
                                        if i < mlineLength and values and mline[i+1] not in values:
                                            sys.stdout.write("\nERROR: Invalid Selection %s, must be one of %s\n" % (mline[i+1], ",".join(values)))
                                            return ''
                                        min,max = self.getValueMinMax(mline[i], submodel, subschema)
                                        if min is not None and max is not None:
                                            try:
                                                num = string.atoi(mline[i+1])
                                                if num < min or num > max:
                                                    sys.stdout.write("\nERROR: Invalid Value %s, must be beteween %s-%s\n" % (mline[i+1], min, max))
                                                    return ''
                                            except:
                                                sys.stdout.write("\nERROR: Invalid Value %s, must be beteween %s-%s\n" % (mline[i+1], min, max))
                                                return ''


                                        # found that if commands are entered after the last command then there can be a problem
                                        self.commandLen = len(mline[:i]) + 1
                                    else:
                                        self.commandLen = len(mline[:i])
                                    self.subcommand = True
                cmd = argv[-1]
                if cmd in ('?', ) or \
                        (mlineLength < self.commandLen and cmd not in ("exit", "end", "help", "no")):
                    self.display_help(argv)
                    return ''


        return argv
