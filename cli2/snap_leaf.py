#!/usr/bin/python

import sys
import cmdln
import json
import jsonref

from sets import Set
from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine
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


        self.setupCommands()

    def applybaseconfig(self, cliname):
        configObj = self.getConfigObj()
        for model, schema in zip(self.modelList, self.schemaList):

            # lets get all commands and subcommands for a given config operation
            allCmdsList = self.getCliCmdAttrs(None, self.objname, False, None, model[self.objname]["commands"], schema[self.objname]["properties"]["commands"]["properties"])
            objDict = {}

            for cmds in allCmdsList:
                for k, v in cmds.iteritems():
                    if v['objname'] not in objDict:
                        objDict[v['objname']] = {}

                    objDict[v['objname']].update({k:v})

            if configObj:
                for k, v in objDict.iteritems():
                    config = CmdEntry(k, objDict[k])
                    if cliname == self.parent.lastcmd[-2]:
                        for kk in v.keys():
                            if kk == cliname:
                                basekey = self.parent.lastcmd[-2]
                                basevalue = self.parent.lastcmd[-1]
                                # TODO this should be set based on some schema/model
                                # letting me know that the parent config can
                                # create a default object, otherwise enging will
                                # try to create a lot of objects
                                config.setValid(v[basekey]['createwithdefaults'])
                                delete = True if self.cmdtype == 'delete' else False
                                config.set(self.parent.lastcmd, delete, basekey, basevalue)

                    # only add this config if it does not already exist
                    cfg = configObj.doesConfigExist(config)
                    if not cfg:
                        configObj.configList.append(config)
                    elif cfg and self.cmdtype == 'delete':
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
        return True

    def setupCommands(self):
        '''
        This api will setup all the do_<command> and comlete_<command> as required by the cmdln class.
        The functionality is common for all commands so we will map the commands based on what is in
        the model.
        The function being supplied is actually a class so that we know the origional callers function
        name.
        :return:
        '''
        # this loop will setup each of the cliname commands for this model level
        # cmdln/cmd expects that all commands have a function associated with it
        # in the format of 'do_<command>'
        # TODO need to add support for when the cli mode does not supply the cliname
        #      in this case need to get the default from the schema model
        for model, schema in zip(self.modelList, self.schemaList):
            for subcmds, cmd in model[self.objname]["commands"].iteritems():
                # handle the links
                if 'subcmd' in subcmds:
                    try:
                        if "commands" in cmd:
                            for k,v in cmd["commands"].iteritems():
                                cmdname = self.getCliName(v)
                                # Note needed for show
                                if '-' in cmdname:
                                    sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI\n" %(cmdname,))
                                    self.do_exit([])
                                    cmdname = cmdname.replace('-', '_')
                                setattr(self.__class__, "do_" + cmdname, SetAttrFunc(self._cmd_common))
                                #setattr(self.__class__, "complete_" + cmdname, self.__getattribute__("_cmd_complete_%s" %(k,)))
                        else:
                            # another sub command list
                            for k, v in cmd.iteritems():
                                cmdname = self.getCliName(v)
                                if '-' in cmdname:
                                    sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                                    self.do_exit([])
                                    cmdname = cmdname.replace('-', '_')
                                # Note needed for show
                                #if cmdname != self.objname:
                                setattr(self.__class__, "do_" + cmdname, SetAttrFunc(self._cmd_common))
                                setattr(self.__class__, "complete_" + cmdname, self._cmd_complete_common)

                    except Exception as e:
                            sys.stdout.write("EXCEPTION RAISED: %s" %(e,))
                else:
                    # handle commands when are not links
                    try:
                        cmdname = self.getCliName(model[self.objname][subcmds]["commands"])
                        if '-' in cmdname:
                            sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                            self.do_exit([])
                            cmdname = cmdname.replace('-', '_')
                        setattr(self.__class__, "do_" + cmdname, SetAttrFunc(self._cmd_common))
                    except Exception as e:
                            sys.stdout.write("EXCEPTION RAISED: %s" %(e,))

        setattr(self.__class__, "do_no", self._cmd_do_delete)
        setattr(self.__class__, "complete_no", self._cmd_complete_delete)

    def teardownCommands(self):
        '''
        This api will setup all the do_<command> and comlete_<command> as required by the cmdln class.
        The functionality is common for all commands so we will map the commands based on what is in
        the model.
        The function being supplied is actually a class so that we know the origional callers function
        name.
        :return:
        '''
        # this loop will setup each of the cliname commands for this model level
        # cmdln/cmd expects that all commands have a function associated with it
        # in the format of 'do_<command>'
        # TODO need to add support for when the cli mode does not supply the cliname
        #      in this case need to get the default from the schema model
        for model, schema in zip(self.modelList, self.schemaList):
            for subcmds, cmd in model[self.objname]["commands"].iteritems():
                # handle the links
                if 'subcmd' in subcmds:
                    try:
                        if "commands" in cmd:
                            for k,v in cmd["commands"].iteritems():
                                cmdname = self.getCliName(v)
                                # Note needed for show
                                if '-' in cmdname:
                                    sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI\n" %(cmdname,))
                                    self.do_exit([])
                                    cmdname = cmdname.replace('-', '_')
                                delattr(self.__class__, "do_" + cmdname)
                                #setattr(self.__class__, "complete_" + cmdname, self.__getattribute__("_cmd_complete_%s" %(k,)))
                        else:
                            # another sub command list
                            for k, v in cmd.iteritems():
                                cmdname = self.getCliName(v)
                                if '-' in cmdname:
                                    sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                                    self.do_exit([])
                                    cmdname = cmdname.replace('-', '_')
                                # Note needed for show
                                #if cmdname != self.objname:
                                delattr(self.__class__, "do_" + cmdname)
                                delattr(self.__class__, "complete_" + cmdname)

                    except Exception as e:
                            sys.stdout.write("EXCEPTION RAISED: %s" %(e,))
                else:
                    # handle commands when are not links
                    try:
                        cmdname = self.getCliName(model[self.objname][subcmds]["commands"])
                        if '-' in cmdname:
                            sys.stdout.write("MODEL conflict invalid character '-' in name %s not supported by CLI" %(cmdname,))
                            self.do_exit([])
                            cmdname = cmdname.replace('-', '_')
                        delattr(self.__class__, "do_" + cmdname)
                    except Exception as e:
                            sys.stdout.write("EXCEPTION RAISED: %s" %(e,))

        delattr(self.__class__, "do_no")
        delattr(self.__class__, "complete_no")

    def do_exit(self, args):
        self.teardownCommands()
        self.prompt = self.baseprompt
        self.stop = True

    def getObjName(self, schema):
        cmd = 'objname'
        return self.getSubCommand(cmd, schema[self.objname]["properties"]["commands"]["properties"])[0][cmd]['default']


    def getCliCmdAttrs(self, key, objname, createwithdefault, subcmd, model, schema):
        '''
        Based on the schema and model will fill in the default object parameters
        :param key:
        :param objname:
        :param subcmd:
        :param model:
        :param schema:
        :return: list of commands available from this leaf class
        '''
        cmdList = []
        cmdDict = {}
        tmpobjname = objname
        tmpcreatewithdefault = createwithdefault

        for k, v in schema.iteritems():
            if k == key:
                return v

            if k in model:
                tmpmodel = model[k]
                try:
                    if 'objname' in v:
                        tmpobjname = v['objname']['default']
                    if 'createwithdefault' in v:
                        tmpcreatewithdefault = v['createwithdefault']['default']
                        if 'createwithdefault' in tmpmodel:
                            tmpcreatewithdefault = tmpmodel['createwithdefault']

                except Exception:
                    pass
                # looking for subcommand attributes
                if "subcmd" in k and "commands" in v and type(v["commands"]) in (dict, jsonref.JsonRef):
                    cmds = self.getCliCmdAttrs(key, tmpobjname, tmpcreatewithdefault, subcmd, tmpmodel["commands"], v["commands"]["properties"])
                    cmdList += cmds
                # looking for subsubcommand
                elif "subcmd" in k and type(v) in (dict, jsonref.JsonRef):

                    for kk, vv in tmpmodel.iteritems():
                        subtmpschema = v[kk]['properties']
                        try:
                            if 'objname' in subtmpschema:
                                tmpobjname = subtmpschema['objname']['default']
                        except Exception:
                            pass

                        tmpsubcmd = None
                        if 'cliname' in vv:
                            if subcmd is None:
                                tmpsubcmd = vv['cliname']
                            else:
                                tmpsubcmd = subcmd + vv['cliname']

                        if "commands" in vv:
                            cmds = self.getCliCmdAttrs(key,
                                                       tmpobjname,
                                                       tmpcreatewithdefault,
                                                       tmpsubcmd,
                                                       vv["commands"],
                                                       subtmpschema["commands"]["properties"])
                            cmdList += cmds

                else:
                    cmdDict.update({tmpmodel['cliname'] : {'key': k,
                                                    'createwithdefaults' : tmpcreatewithdefault,
                                                    'subcommand' : subcmd,
                                                    'objname' : objname,
                                                    'value': v['properties']['defaultarg']['default'],
                                                    'isarray': v['properties']['islist']['default'],
                                                    'type': v['properties']['argtype']['default']}})
            elif 'properties' in v:
                cmdDict.update({v['properties']['cliname']['default'] : {'key': k,
                                                    'createwithdefaults' : tmpcreatewithdefault,
                                                    'subcommand' : subcmd,
                                                    'objname' : objname,
                                                    'value': v['properties']['defaultarg']['default'],
                                                    'isarray': v['properties']['islist']['default'],
                                                    'type': v['properties']['argtype']['default']}})
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

    def _cmd_common(self, argv):
        delete = False
        mline = argv
        if len(argv) > 0 and argv[0] == 'no':
            mline = argv[1:]
            delete = True

        if len(mline) < 2:
            return
        elif len(mline) == 2:
            # key value supplied
            key = None
            subkey = mline[0]
            value = mline[1]

            configObj = self.getConfigObj()
            if configObj:
                for config in configObj.configList:
                    if subkey in config.keysDict.keys():
                        config.setValid(True)
                        if len(config.attrList) > 1 and delete:
                            config.clear(subkey, value)
                        else:
                            # store the attribute into the config
                            config.set(self.lastcmd, delete, subkey, value)
        else:
            # key + subkey + value supplied
            key = mline[0]
            subkey = mline[1]
            value = mline[2]
            configObj = self.getConfigObj()
            if configObj:
                for config in configObj.configList:
                    if subkey in config.keysDict.keys():
                        config.setValid(True)
                        if len(config.attrList) > 1 and delete:
                            config.clear(subkey, value)
                        else:
                            config.set(self.lastcmd, delete, subkey, value)


    def getchildrencmds(self, parentname, model, schema):
        attrlist = []
        if model:
            schemaname = self.getSchemaCommandNameFromCliName(parentname, model)
            for cmdobj in [obj for k, obj in model[schemaname]["commands"].iteritems() if "subcmd" in k]:
                for v in cmdobj["commands"].values():
                    if v['cliname'] != self.objname:
                        attrlist.append(v['cliname'])
        return attrlist

    # this complete is meant for sub ethernet commands
    # for example:
    # >ip address 10.1.1.1
    def _cmd_complete_common(self, text, line, begidx, endidx):
        #sys.stdout.write("\nline: %s text: %s %s\n" %(line, text, not text))
        # remove spacing/tab
        mline = [self.objname] + [x for x in line.split(' ') if x != '']
        mlineLength = len(mline)
        #sys.stdout.write("\nmline: %s\n" %(mline))

        subcommands = []
        # no comamnd case
        if len(mline) == 1:
            for f in dir(self.__class__):
                if f.startswith('do_') and not f.endswith('no'):
                    subcommands.append(f.lstrip('do_'))

        for i in range(1, mlineLength):
            for model, schema in zip(self.modelList, self.schemaList):
                #sys.stdout.write("model %s\n schema %s\n mline[%s] %s\n" %(model, schema, i, mline[i]))
                schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], model)
                #sys.stdout.write("\nschemaname %s\n\n" %(schemaname))
                submodelList = self.getSubCommand(mline[i], model[schemaname]["commands"])
                #sys.stdout.write("submoduleList %s\n" %(submodelList,))
                if submodelList:
                    subschemaList = self.getSubCommand(mline[i], schema[schemaname]["properties"]["commands"]["properties"])
                    #sys.stdout.write("subschemaList %s\n" %(subschemaList,))
                    for submodel, subschema in zip(submodelList, subschemaList):
                        #sys.stdout.write("submodel %s\n subschema %s\n mline %s" %(submodel, subschema, mline[i]))
                        subcommands += self.getchildrencmds(mline[i], submodel, subschema)
                        #sys.stdout.write("subcommands %s" %(subcommands,))

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
        mline = [self.objname] + argv
        mlineLength = len(mline)
        #sys.stdout.write("complete cmd: %s\ncommand %s objname %s\n\n" %(self.model, mline[0], self.objname))

        #submodel = self.model
        #subschema = self.schema
        subcommands = []
        for model, schema in zip(self.modelList, self.schemaList):
            subcommands = self.getchildrenhelpcmds(mline[0], model, schema)

        for i in range(1, mlineLength-1):
            for model, schema in zip(self.modelList, self.schemaList):
                schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], model)
                #sys.stdout.write("model %s\n schema %s\n mline[%s] %s\n" %(model, schema, i, mline[i]))
                submodelList = self.getSubCommand(mline[i], model[schemaname]["commands"])
                if submodelList:
                    subschemaList = self.getSubCommand(mline[i], schema[schemaname]["properties"]["commands"]["properties"])
                    for submodel, subschema in zip(submodelList, subschemaList):
                        #sys.stdout.write("submodel %s\n subschema %s\n mline %s" %(submodel, subschema, mline[i]))
                        subcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema)

        self.printCommands(mline, subcommands)

    def do_help(self, argv):
        self.display_help(argv)

    def precmd(self, argv):
        return CommonCmdLine.precmd(self, argv)
