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
# This is class handles the action of the show command
import sys
from sets import Set
import cmdln
import json
import pprint
import inspect
import string
import snapcliconst
from jsonref import JsonRef

from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine, SUBCOMMAND_VALUE_NOT_EXPECTED, \
    SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE, SUBCOMMAND_VALUE_EXPECTED
from snap_leaf import LeafCmd
from cmdEntry import CmdEntry

try:
    from flexswitchV2 import FlexSwitch
    MODELS_DIR = './'
except:
    sys.path.append('/opt/flexswitch/sdk/py/')
    MODELS_DIR='/opt/flexswitch/models/'
    from flexswitchV2 import FlexSwitch

gObjectsInfo =  {}

class CliNode(object):
    def __init__(self):
        pass

class CliTreeInfo(object):
    def __init__(self,):
        pass

configTree = []

def convertPortToSpecialFmt(modelname, value):
    if modelname in snapcliconst.DYNAMIC_MODEL_ATTR_NAME_LIST:
        tmp = "1/" + value.replace(snapcliconst.PORT_NAME_PREFIX, "")
        return tmp
    return value

def convertStrValueToValueType(attrtype, value):

    rvalue = value
    if snapcliconst.isboolean(attrtype):
        if isinstance(value, unicode) or isinstance(value, str):
            rvalue = snapcliconst.convertStrBoolToBool(value)
    elif snapcliconst.isnumeric(attrtype):
        if isinstance(value, unicode) or isinstance(value, str):
            rvalue = snapcliconst.convertStrNumToNum(value)

    return rvalue


def convertCmdToSpecialFmt(modelname, v):
    attrtype, cliname, value, defaultvalue = v['type'], v['cliname'], v['value'], v['defaultvalue']
    line = ''
    if snapcliconst.isboolean(attrtype):
        if (type(value) == str and value.lower() == 'false') or \
                value == False:
            line = " no %s" %(cliname, )
        else:
            line = " %s" %(cliname, )
    elif attrtype in ('string', 'str'):
        if type(value) not in (list, dict):
            if value.lower() in snapcliconst.CLI_COMMAND_NEGATIVE_TRUTH_VALUES:
                if cliname != 'shutdown':
                    line = " no %s" %(cliname, )
                else:
                    line = " %s" %(cliname, )
            elif value.lower() in snapcliconst.CLI_COMMAND_POSITIVE_TRUTH_VALUES:
                if cliname != 'shutdown':
                    line = " %s" %(cliname)
                else:
                    line = " no %s" %(cliname, )
            elif modelname in snapcliconst.DYNAMIC_MODEL_ATTR_NAME_LIST:
                newvalue = convertPortToSpecialFmt(modelname, value)
                line = " %s %s" %(cliname, newvalue)
        elif type(value) == list:
            newvalue = ",".join(["%s" % (convertPortToSpecialFmt(modelname, x)) for x in value])
            line = " %s %s" %(cliname, newvalue)

    elif snapcliconst.isnumeric(attrtype):
        if type(value) not in (list, dict):
            line = " %s %s" %(cliname, value)
        elif type(value) == list:
            newvalue = ",".join(["%s" % (convertPortToSpecialFmt(modelname, x)) for x in value])
            line = " %s %s" %(cliname, newvalue)
    #else: # struct, which in json/python world is a dict
    # TODO need to deal with struct return



    if line == '':
        line = " %s %s" %(cliname, value)

    return line

def convertRawConfigtoTreeCli(cls):
    def getcfgline(lvl, c):
        if lvl >= 1:
            line = "  " * (lvl)
        else:
            line = ""

        if 'cliname' in c.objKeyVal:
            value = convertStrValueToValueType(c.objKeyVal['type'],
                                               convertPortToSpecialFmt(c.objKeyVal['modelname'],c.objKeyVal['value']))
            line += c.cmd + " %s" %(value)
            yield lvl, line
            lvl += (1 if len(line) > 0 else 0)

        for k, v in c.attributes.iteritems():
            if convertStrValueToValueType(v['type'], v['value']) != convertStrValueToValueType(v['type'], v['defaultvalue']) and \
                    (('cliname' not in c.objKeyVal) or (v['cliname'] != c.objKeyVal['cliname'])):
                if lvl >= 1:
                    line = "  " * lvl
                else:
                    line = ""

                if ('cliname' not in c.objKeyVal):
                    line += c.cmd

                line += convertCmdToSpecialFmt(k, v)
                yield lvl, line
        for sc in c.subcfg:
            if lvl >= 1:
                sc.cmd = " " * lvl + sc.cmd
            for rlvl, l in getcfgline(lvl, sc):
                yield rlvl, l

        yield lvl, ''

    lvl = 0
    for (rlvl, l) in getcfgline(lvl, cls):
        if len(l.lstrip()) > 0:
            if rlvl == 0:
                print '!'
            print l.replace("config", "")


def convertRawConfigToTreeJson(cls):
    pass

def convertRawConfigToTreeJsonFull(cls):
    pass

def convertRawConfigToTreeCliFull(cls):
    def getcfgline(lvl, c):
        if lvl >= 1:
            line = " " * (lvl)
        else:
            line = ""

        if 'cliname' in c.objKeyVal:
            value = convertPortToSpecialFmt(c.objKeyVal['modelname'],c.objKeyVal['value'])
            line += c.cmd + " %s" %(value)
            yield lvl, line
            lvl += (1 if len(line) > 0 else 0)

        for k, v in c.attributes.iteritems():
            if (('cliname' not in c.objKeyVal) or (v['cliname'] != c.objKeyVal['cliname'])):
                if lvl >= 1:
                    line = " " * lvl
                else:
                    line = ""

                if ('cliname' not in c.objKeyVal):
                    line += c.cmd

                line += convertCmdToSpecialFmt(k, v)
                yield lvl, line
        #lvl += (1 if len(line) > 0 else 0)
        for sc in c.subcfg:
            if lvl >= 1:
                sc.cmd = " " * lvl + sc.cmd
            for rlvl, l in getcfgline(lvl, sc):
                yield rlvl, l

        yield lvl, ''

    lvl = 0
    for (rlvl, l) in getcfgline(lvl, cls):
        if len(l.lstrip()) > 0:
            if rlvl == 0:
                print '!'
            print l.replace("config", "")



class ConfigElement(object):
    STRING_FORMAT_CLI_NO_DEFAULT = 1
    STRING_FORMAT_CLI_FULL = 2
    STRING_FORMAT_CLI_JSON_NO_DEFAULT = 3
    STRING_FORMAT_CLI_JSON_FULL = 4
    def __init__(self,):
        self.cmd = ''
        self.fmt =self.STRING_FORMAT_CLI_NO_DEFAULT
        self.objname = None
        self.objKeyVal = {}
        self.attributes = {}
        self.subcfg = []

    def setFormat(self, fmt=None):
        self.fmt = fmt
        if fmt == self.STRING_FORMAT_CLI_FULL:
            setattr(self.__class__, 'dump', convertRawConfigToTreeCliFull)
        elif fmt == self.STRING_FORMAT_CLI_JSON_NO_DEFAULT:
            setattr(self.__class__, 'dump', convertRawConfigToTreeJson)
        elif fmt == self.STRING_FORMAT_CLI_JSON_FULL:
            setattr(self.__class__, 'dump', convertRawConfigToTreeJsonFull)
        else:
            setattr(self.__class__, 'dump', convertRawConfigtoTreeCli)

    def setCmd(self, c):
        self.cmd = c.lstrip()

    def setObjName(self, o):
        self.objname = o

    def setObjKeyVal(self, m, t, k, v, df):
        self.objKeyVal = {'modelname': m,
                          'type': t,
                          'cliname': k,
                          'value': v,
                          'defaultvalue': df}

    def setAttributes(self, modelname, cliname, t, v, df):
        self.attributes.update({modelname: {'cliname': cliname,
                                            'type': t,
                                            'value': v,
                                            'defaultvalue': df}})
    def setSubCfg(self, c):
        self.subcfg.append(c)

    def dump(self):
        pass

class ShowRun(object):
    # const variables used to determine if an object has been used or not as part of building up the tree
    # Note: some objects may be used in multiple places
    USED_CONFIG = 1
    UNUSED_CONFIG =2
    def __init__(self, swtch):
        """
        :param swtch: Flexswitch SDK
        :param model: config tree json model
        :param schema: schema tree json model
        :return:
        """
        self.swtch = swtch
        self.objects = {}
        self.currRawCfg = {}

        with open(MODELS_DIR + 'genObjectConfig.json') as objInfoFile:
            self.objects = json.load(objInfoFile)

    def getRawConfigFromNode(self):

        for objName, objInfo  in self.objects.iteritems ():
            if 'w' in objInfo['access'] :
                methodName = 'getAll'+objName+'s'
                method =  getattr(self.swtch, methodName, None)
                if method :
                    try:
                        cfgList = method()
                    except Exception as e:
                        sys.stdout.write("failed to get object info for %s\n" %(objName))
                        continue
                    if cfgList != None and len(cfgList):
                        self.currRawCfg [objName] = []
                        for cfg in cfgList:
                            currentObj = json.loads(json.dumps(cfg['Object']))
                            self.currRawCfg[objName].append((self.UNUSED_CONFIG, currentObj))


    def getNewConfigObj(self, objname, matchattr, matchvalue):
        '''
        Get the config object from the raw config list, but need to ensure that the object
        does not alredy exist in the config tree
        :param objname:
        :return:
        '''
        if objname in self.currRawCfg:
            for (status, cfgObj) in self.currRawCfg[objname]:
                if status == self.UNUSED_CONFIG and matchattr is None:
                    status = self.USED_CONFIG
                    yield cfgObj
                else:
                    for attr, value in cfgObj.iteritems():
                        if matchattr == attr and matchvalue == value:
                            yield cfgObj


        yield None

    def fillObjAttrs(self, element, keyval, cfgObj):
        pass

    def buildTreeObj(self, cmd, pelement, matchattrtype, matchattr, matchvalue, model, schema, subattrobj=False):

        def isModelObj(mobj, sobj):
            return 'objname' in sobj['properties']

        def isLeafAttrObj(mobj, sobj):
            return 'commands' in mobj.keys()

        def getModelAttrFromMatchAttr(matchattr, mobj, sobj):
            for (mcmds, mvalues) in mobj['commands'].iteritems():
                svalues = sobj['properties']['commands']['properties'] if 'properties' in sobj else sobj['commands']['properties'][mcmds]
                if 'subcmd' in mcmds and isLeafAttrObj(mvalues, svalues):
                    for mattr, mattrobj in mvalues['commands'].iteritems():
                        if 'cliname' in mattrobj and \
                                        mattrobj['cliname'] == matchattr:
                            return mattr
                else:
                    # commands are already the attributes
                    if 'cliname' in mvalues and \
                                    mvalues['cliname'] == matchattr:
                        return mcmds

        if 'commands' not in schema.keys():
            for (mkey, mobj) in model.iteritems():
                if mkey in schema:
                    sobj = schema[mkey]

                    if 'cliname' in mobj:
                        if mobj['cliname'] != 'config':
                            cmd += " " + mobj['cliname']

                    # found an object via schema
                    if isModelObj(mobj, sobj):
                        objname = sobj['properties']['objname']['default']

                        for cfgObj in self.getNewConfigObj(objname,
                                                           getModelAttrFromMatchAttr(matchattr, mobj, sobj),
                                                           convertStrValueToValueType(matchattrtype, matchvalue)):
                            # lets get an element from the raw config json objects
                            if cfgObj or subattrobj:
                                element = ConfigElement()
                                pelement.setSubCfg(element)
                                element.setFormat(pelement.fmt)
                                element.setCmd(cmd)
                                # found an element lets populate the contents of the element from this object
                                element.setObjName(objname)
                                for attr, attrobj in mobj['value'].iteritems():
                                    defaultVal = sobj['properties']['value']['properties'][attr]['properties']['defaultarg']['default']
                                    attrtype = sobj['properties']['value']['properties'][attr]['properties']['argtype']['type']
                                    value = cfgObj[attr] if cfgObj else subattrobj[attr]
                                    element.setObjKeyVal(attr,
                                                         attrtype,
                                                         attrobj['cliname'],
                                                         convertStrValueToValueType(attrtype, value),
                                                         convertStrValueToValueType(attrtype, defaultVal))

                                # lets get key attributes for this model object
                                # the attributes that we are interested in will come from the model
                                # lets find the attr obj
                                for (mcmds, mvalues) in mobj['commands'].iteritems():
                                    svalues = sobj['properties']['commands']['properties'][mcmds]
                                    if 'subcmd' in mcmds and isLeafAttrObj(mvalues, svalues):
                                        for mattr, mattrobj in mvalues['commands'].iteritems():
                                            if 'cliname' in mattrobj and \
                                                            mattrobj['cliname'] != matchattr:
                                                defaultVal = svalues['commands']['properties'][mattr]['properties']['defaultarg']['default']
                                                attrtype = svalues['commands']['properties'][mattr]['properties']['argtype']['type']
                                                value = cfgObj[mattr] if cfgObj else subattrobj[mattr]
                                                element.setAttributes(mattr,
                                                                      mattrobj['cliname'],
                                                                      attrtype,
                                                                      convertStrValueToValueType(attrtype, value),
                                                                      convertStrValueToValueType(attrtype, defaultVal))

                                # sub model objects
                                for (mcmds, mvalues) in mobj['commands'].iteritems():
                                    svalues = sobj['properties']['commands']['properties'][mcmds]
                                    if 'subcmd' in mcmds:
                                        if not isLeafAttrObj(mvalues, svalues):
                                            self.buildTreeObj('',
                                                              element,
                                                              element.objKeyVal['type'],
                                                              element.objKeyVal['cliname'],
                                                              element.objKeyVal['value'],
                                                              mvalues,
                                                              svalues)
                                        else:
                                            if len(mvalues['listattrs']) > 0:
                                                for (submcmds, submvalues) in mvalues['commands'].iteritems():
                                                    subsvalues = svalues['commands']['properties'][submcmds]
                                                    for subcmd, subattr in mvalues['listattrs']:
                                                        if submcmds == subcmd:
                                                            # reached a sub attribute
                                                            # lets get the match attr for this object
                                                            if type(cfgObj[subattr]) is list:
                                                                for subobj in cfgObj[subattr]:
                                                                    self.buildTreeObj('',
                                                                                      element,
                                                                                      None,
                                                                                      None,
                                                                                      None,
                                                                                      submvalues,
                                                                                      subsvalues,
                                                                                      subattrobj=subobj)
                                                            else:
                                                                self.buildTreeObj('',
                                                                                  element,
                                                                                  None,
                                                                                  None,
                                                                                  None,
                                                                                  submvalues,
                                                                                  subsvalues,
                                                                                  subattrobj=cfgObj[subattr])

                    else:
                        # since we are not a model object we are either a leaf or a branch
                        # branch objects we need to retain the parent matchattr and matchvalue
                        for (mcmds, mvalues) in mobj['commands'].iteritems():
                            svalues = sobj['properties']['commands']['properties'][mcmds]
                            if 'subcmd' in mcmds:
                                if not isLeafAttrObj(mvalues, svalues):
                                    self.buildTreeObj(cmd,
                                                      pelement,
                                                      None,
                                                      None,
                                                      None,
                                                      mvalues,
                                                      svalues)
                                else:
                                    self.buildTreeObj(cmd,
                                                      pelement,
                                                      matchattrtype,
                                                      matchattr,
                                                      matchvalue,
                                                      mvalues,
                                                      svalues)
        else:
            # lets handle a leaf members
            if 'objname' in schema:
                objname = schema['objname']['default']

                # lets get an element from the raw config json objects
                modelMatchAttrName = getModelAttrFromMatchAttr(matchattr, model, schema)
                for cfgObj in self.getNewConfigObj(objname,
                                                   modelMatchAttrName,
                                                   convertStrValueToValueType(matchattrtype, matchvalue)):
                    if cfgObj or subattrobj:
                        element = ConfigElement()
                        pelement.setSubCfg(element)
                        element.setFormat(pelement.fmt)
                        element.setCmd(cmd)
                        # found an element lets populate the contents of the element from this object
                        element.setObjName(objname)

                        if 'value' in model:
                            for attr, attrobj in model['value'].iteritems():
                                defaultVal = schema['properties']['value']['properties'][attr]['properties']['defaultarg']['default']
                                attrtype = schema['properties']['value']['properties'][attr]['properties']['argtype']['type']
                                value = cfgObj[attr] if cfgObj else subattrobj[attr]
                                element.setObjKeyVal(attr,
                                                     attrtype,
                                                     attrobj['cliname'],
                                                     convertStrValueToValueType(attrtype, value),
                                                     convertStrValueToValueType(attrtype, defaultVal))


                        # lets get key attributes for this model object
                        # the attributes that we are interested in will come from the model
                        # lets find the attr obj
                        for (mcmds, mvalues) in model['commands'].iteritems():
                            svalues = schema['commands']['properties'][mcmds]
                            if 'subcmd' in mcmds and isLeafAttrObj(mvalues, svalues):
                                for mattr, mattrobj in mvalues['commands'].iteritems():
                                    if mcmds != modelMatchAttrName:
                                        defaultVal = svalues['commands']['properties'][mattr]['properties']['defaultarg']['default']
                                        attrtype = svalues['commands']['properties'][mattr]['properties']['argtype']['type']
                                        value = cfgObj[mattr] if cfgObj else subattrobj[mattr]
                                        element.setAttributes(mattr,
                                                              mattrobj['cliname'],
                                                              attrtype,
                                                              convertStrValueToValueType(attrtype, value),
                                                              convertStrValueToValueType(attrtype, defaultVal))
                            else:
                                if mcmds != modelMatchAttrName:
                                    element.setCmd(cmd)
                                    defaultVal = svalues['properties']['defaultarg']['default']
                                    attrtype = svalues['properties']['argtype']['type']
                                    value = cfgObj[mcmds] if cfgObj else subattrobj[mcmds]
                                    element.setAttributes(mcmds,
                                                          mvalues['cliname'],
                                                          attrtype,
                                                          convertStrValueToValueType(attrtype, value),
                                                          convertStrValueToValueType(attrtype, defaultVal))

pp = pprint.PrettyPrinter(indent=2)
class ShowCmd(cmdln.Cmdln, CommonCmdLine):

    def __init__(self, parent, model, schema):

        cmdln.Cmdln.__init__(self)
        self.objname = 'show'
        self.parent = parent
        self.model = model
        self.schema = schema
        self.configList = []

    def doesConfigExist(self, c):
        '''
        :param entry: CmdEntry
        :return: already provisioned CmdEntry or None if it does not exist
        '''
        for config in self.configList:
            if config.name == c.name:
                return config
        return None

    def show(self, argv, all=False):
        # show command will work on various types of show
        # show all
        # show individual object
        # show individual object brief

        if 'run' in argv:
            sdk = self.getSdk()
            run = ShowRun(sdk)
            run.getRawConfigFromNode()
            ce = ConfigElement()

            cmd = " ".join(argv)
            # TODO MOVE THESE TO NEW Cmdln objects
            if cmd == ("show run",):
                print 'printing without defaluts'
                ce.setFormat(ConfigElement.STRING_FORMAT_CLI_NO_DEFAULT)
            elif cmd in ("show run all",):
                print 'printing with defaluts'
                ce.setFormat(ConfigElement.STRING_FORMAT_CLI_FULL)
            elif cmd in ("show run json",):
                ce.setFormat(ConfigElement.STRING_FORMAT_CLI_JSON_NO_DEFAULT)
            elif cmd in ("show run json all",):
                ce.setFormat(ConfigElement.STRING_FORMAT_CLI_JSON_FULL)

            run.buildTreeObj('', ce, None, None, None, self.model, self.schema)
            ce.dump()

        else:
            lastcmd = argv[-1] if all else argv[-2] if argv[-1] != 'brief' else argv[-3]
            schemaname = self.getSchemaCommandNameFromCliName(lastcmd, self.model)
            if schemaname:
                # leaf will gather all the config info for the object
                #l = LeafCmd(schemaname, lastcmd, "show", self, None, [self.model], [self.schema])
                #l.applybaseshow(lastcmd)

                # only display the what is available from this object
                for k, v in self.schema[schemaname]['properties']['commands']['properties'].iteritems():
                    # looping through the subcmds to find one that has an object associated with it.
                    if type(v) in (dict, JsonRef):
                        for kk, vv in v.iteritems():
                            # each subcmd will either be a link to another subcommand
                            # or a commands containing attributes of an object, which should hold
                            # the object in question associated with this command.
                            if "objname" in kk:
                                config = CmdEntry(v['objname']['default'], {})
                                config.setValid(True)
                                self.configList.append(config)

                # todo need to call the keys
                # l.do_lastcmd
                #if not all:
                #    func = getattr(l, "do_%s" %(lastcmd,))
                #    func(argv[-2:])

                self.show_state(all=all)
                self.configList.remove(config)

    def get_sdk_func_key_values(self, data, func):
        argspec = inspect.getargspec(func)
        getKeys = argspec.args[1:]
        lengthkwargs = len(argspec.defaults) if argspec.defaults is not None else 0
        if lengthkwargs > 0:
            getKeys = argspec.args[:-len(argspec.defaults)]

        # lets setup the argument list
        # and remove the values from the kwargs
        argumentList = []
        # set all the args
        if 'create' in func.__name__ or \
           'get' in func.__name__ or \
           'print' in func.__name__:
            for k in getKeys:
                if k in data:
                    argumentList.append(data[k])

            data = {}
        elif 'update' in func.__name__:
            for k in getKeys:
                if k in data:
                    argumentList.append(data[k])
                    if k in data:
                        del data[k]


        return (argumentList, data)


    def show_state(self, all=False):
        showObj = self.getShowObj()
        if showObj and showObj.configList:
            sys.stdout.write("Applying Show:\n")
            # tell the user what attributes are being applied
            for i in range(len(showObj.configList)):
                config = showObj.configList[-(i+1)]
                #config.show()

                # get the sdk
                sdk = self.getSdkShow()

                funcObjName = config.name + 's' if 'State' in config.name else config.name + 'States'
                try:
                    if all:
                        printall_func = getattr(sdk, 'print' + funcObjName)
                        printall_func()
                    else:
                        # update all the arguments so that the values get set in the get_sdk_...
                        print_func = getattr(sdk, 'print' + funcObjName)
                        data = config.getSdkConfig()
                        (argumentList, kwargs) = self.get_sdk_func_key_values(data, print_func)
                        print_func(*argumentList)

                    # remove the configuration as it has been applied
                    config.clear(None, None, all=True)
                except Exception as e:
                    sys.stdout.write("FAILED TO GET OBJECT for show state: %s\n" %(e,))
