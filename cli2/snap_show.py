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
import sys, os
import json
import pprint
import inspect
import snapcliconst
import jsonref

from commonCmdLine import CommonCmdLine
from cmdEntry import CmdEntry
import snapcliconst
MODELS_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"

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
        tmp = value
        if type(value) is str:
            tmp = value.replace(snapcliconst.PORT_NAME_PREFIX, "")
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
                                               convertPortToSpecialFmt(c.objKeyVal['modelname'], c.objKeyVal['value']))
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
        '''
            this function may need to be updated to support more than one key
        '''
        # special cases
        if self.objname == "StpBridgeInstance" and \
            m == "Vlan" and v == snapcliconst.DEFAULT_PVID:
                self.objKeyVal = {'modelname': m,
                                  'type': 'string',
                                  'cliname': '',
                                  'value': '',
                                  'defaultvalue': snapcliconst.DEFAULT_PVID}
                self.cmd = self.cmd.split(' ')[0] + " rstp"
        elif self.objname == 'StpPort' and \
            m == "Vlan" and v == snapcliconst.DEFAULT_PVID:
                self.objKeyVal = {'modelname': m,
                                  'type': 'string',
                                  'cliname': '',
                                  'value': '',
                                  'defaultvalue': snapcliconst.DEFAULT_PVID}
                self.cmd = self.cmd.split(' ')[0] + " rstp"
        elif self.objname in ("Port", "IPv4Intf", "IPv6Intf", "BGPv4Neighbor", "BGPv6Neighbor")  and \
            m == "IntfRef":
                self.objKeyVal = {'modelname': m,
                                  'type': t,
                                  'cliname': k,
                                  'value': v,
                                  'defaultvalue': df}
                cmdList = self.cmd.split(' ')
                self.cmd = " ".join( "%s" % cmdList[i] for i in xrange(0, len(cmdList)-1))
        else:
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
    def __init__(self, parent, swtch):
        """
        :param swtch: Flexswitch SDK
        :param model: config tree json model
        :param schema: schema tree json model
        :return:
        """
        self.parent = parent
        self.swtch = swtch
        self.objects = {}
        self.currRawCfg = {}

        # this json contains all the object files known by flexswitch
        with open(MODELS_DIR + 'genObjectConfig.json') as objInfoFile:
            self.objects = json.load(objInfoFile)

    def getRawConfigFromNode(self):

        for objName, objInfo  in self.objects.iteritems():
            if 'w' in objInfo['access']:
                methodName = 'getAll'+objName+'s'
                #print methodName
                method = getattr(self.swtch, methodName, None)
                if method:
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
                        if matchattr == attr:
                            convertedvalue = snapcliconst.updateSpecialValueCases(self.parent, matchattr, matchvalue)
                            if type(value) is list:
                                if type(convertedvalue) is list:
                                    if len(frozenset(value).intersection(convertedvalue)) > 0:
                                        yield cfgObj
                                else:
                                    if convertedvalue in value:
                                        yield cfgObj
                            elif convertedvalue == value:
                                yield cfgObj


        yield None

    def fillObjAttrs(self, element, keyval, cfgObj):
        pass

    def checkForKeySpecialCasesToIgnore(self, cmd, objname, value):
        # special interface command check since there are three
        # port
        # svi
        # lag
        ignoreobj = False
        if 'interface' in cmd and objname in ("IPv4Intf", "IPv6Intf"):
            # need to determine the type of interface this is to see if it applies
            # to this portion of the tree
            methodName = 'get'+objname+'State'
            method = getattr(self.swtch, methodName, None)
            r = method(value)
            data = r.json()
            if data.has_key("Object"):
                iftype = data['Object']['L2IntfType']
                if iftype == "Port" and ("eth" not in cmd and "fpPort" not in cmd):
                    ignoreobj = True
                elif iftype == "Lag" and ("port_channel" not in cmd):
                    ignoreobj = True
                elif iftype == "Vlan" and ("svi" not in cmd and "vlan" not in cmd):
                    ignoreobj = True

        # there are cases where keys are optional so lets check to see if the value
        if value in (None, '', {}, [], ()):
            ignoreobj = True

        return ignoreobj

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
                    # lets check for global attributes
                    '''
                    if not matchattr:
                        if 'commands' in sobj and 'properties' in sobj['commands']:
                            for key, cmds in sobj['commands']['properties'].iteritems():
                                if 'properties' in cmds:
                                    if cmds['properties']['key']['default']:
                                        return key
                    '''

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
                                element.setCmd(cmd)
                                element.setFormat(pelement.fmt)
                                ignoreobj = False
                                keyisdefault = False
                                # found an element lets populate the contents of the element from this object
                                element.setObjName(objname)
                                if 'value' in mobj:
                                    for attr, attrobj in mobj['value'].iteritems():
                                        defaultVal = snapcliconst.getValueAttrDefault(sobj, attr )
                                        attrtype = snapcliconst.getValueAttrType(sobj, attr)
                                        value = cfgObj[attr] if cfgObj else subattrobj[attr]

                                        if value == defaultVal:
                                            keyisdefault = True

                                        if not ignoreobj:
                                            ignoreobj = self.checkForKeySpecialCasesToIgnore(cmd, objname, value)

                                        element.setObjKeyVal(attr,
                                                             attrtype,
                                                             attrobj['cliname'],
                                                             convertStrValueToValueType(attrtype, value),
                                                             convertStrValueToValueType(attrtype, defaultVal))
                                
                                # lets get key attributes for this model object
                                # the attributes that we are interested in will come from the model
                                # lets find the attr obj
                                foundParentKeyCliName = False
                                for (mcmds, mvalues) in mobj['commands'].iteritems():
                                    svalues = sobj['properties']['commands']['properties'][mcmds]
                                    if 'subcmd' in mcmds and isLeafAttrObj(mvalues, svalues):
                                        for mattr, mattrobj in mvalues['commands'].iteritems():
                                            if 'cliname' in mattrobj and \
                                                            mattrobj['cliname'] != matchattr:
                                                defaultVal = svalues['commands']['properties'][mattr]['properties']['defaultarg']['default']
                                                attrtype = svalues['commands']['properties'][mattr]['properties']['argtype']['type']
                                                iskey = svalues['commands']['properties'][mattr]['properties']['key']['default']
                                                if not iskey and (cfgObj and  mattr in cfgObj) or \
                                                        (subattrobj and mattr in subattrobj):
                                                    value = cfgObj[mattr] if cfgObj else subattrobj[mattr]
                                                    element.setAttributes(mattr,
                                                                          mattrobj['cliname'],
                                                                          attrtype,
                                                                          convertStrValueToValueType(attrtype, value),
                                                                          convertStrValueToValueType(attrtype, defaultVal))
                                                elif iskey and pelement and 'cliname' in pelement.objKeyVal:
                                                    # check if the key exists as the key from the parent
                                                    value = cfgObj[mattr] if cfgObj else subattrobj[mattr]
                                                    ignoreobj = True
                                                    # two cases
                                                    # 1) parent key is a key for the element
                                                    # 2) parent key is not a member, the element just lives under
                                                    #    this object in the tree
                                                    if mattrobj['cliname'] == pelement.objKeyVal['cliname']:
                                                        foundParentKeyCliName = True

                                                    if mattrobj['cliname'] == pelement.objKeyVal['cliname'] and \
                                                        value == pelement.objKeyVal['value']:
                                                        ignoreobj = False


                                # element lives under this tree but a non default key
                                # was not set so lets make sure we make this a valid
                                # element
                                if not foundParentKeyCliName and not keyisdefault:
                                    ignoreobj = False

                                # lets set the parent object if
                                # this object is part of this parent
                                if not ignoreobj:
                                    pelement.setSubCfg(element)

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
                                            elif 'objname' in svalues and \
                                                        objname != svalues['objname']['default']:
                                                if 'type' in element.objKeyVal:
                                                    self.buildTreeObj('',
                                                                      element,
                                                                      element.objKeyVal['type'],
                                                                      element.objKeyVal['cliname'],
                                                                      element.objKeyVal['value'],
                                                                      mvalues,
                                                                      svalues)

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
                        else:
                            # lets deal with objects who have a default key
                            if 'commands' in schema and 'properties' in schema['commands']:
                                for attr, attrobj in schema['commands']['properties'].iteritems():
                                    if 'properties' in attrobj and 'key' in attrobj['properties'] and \
                                        attrobj['properties']['key']['default'] and \
                                            attrobj['properties']['defaultarg']['default']:
                                        defaultVal = attrobj['properties']['defaultarg']['default']
                                        attrtype = attrobj['properties']['argtype']['type']
                                        value = cfgObj[attr] if cfgObj else subattrobj[attr]
                                        element.setObjKeyVal(attr,
                                                     attrtype,
                                                     "",
                                                     convertStrValueToValueType(attrtype, value),
                                                     convertStrValueToValueType(attrtype, defaultVal))



                        # lets get key attributes for this model object
                        # the attributes that we are interested in will come from the model
                        # lets find the attr obj
                        for (mcmds, mvalues) in model['commands'].iteritems():
                            svalues = schema['commands']['properties'][mcmds]
                            if 'subcmd' in mcmds:
                                if isLeafAttrObj(mvalues, svalues):
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
class ShowCmd(CommonCmdLine):

    def __init__(self, parent, model, schema, numKeys):

        CommonCmdLine.__init__(self, "", "", "", "", "")
        self.objname = 'show'
        self.parent = parent
        self.model = model
        self.schema = schema
        self.configList = []
        self.numKeys = numKeys
        self.cmdtype = snapcliconst.COMMAND_TYPE_SHOW

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
        # TOOD
        # show command will work on various types of show
        # show all
        # show individual object
        # show individual object brief
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



        if 'run' in argv:
            sdk = self.getSdk()
            run = ShowRun(self, sdk)
            run.getRawConfigFromNode()
            ce = ConfigElement()

            cmd = " ".join(argv)
            # TODO MOVE THESE TO NEW Cmdln objects
            if cmd == ("show run",):
                print 'printing without defaluts'
                ce.setFormat(ConfigElement.STRING_FORMAT_CLI_NO_DEFAULT)
            elif cmd in ("show run full",):
                print 'printing with defaluts'
                ce.setFormat(ConfigElement.STRING_FORMAT_CLI_FULL)
            elif cmd in ("show run json",):
                ce.setFormat(ConfigElement.STRING_FORMAT_CLI_JSON_NO_DEFAULT)
            elif cmd in ("show run json all",):
                ce.setFormat(ConfigElement.STRING_FORMAT_CLI_JSON_FULL)

            run.buildTreeObj('', ce, None, None, None, self.model, self.schema)
            ce.dump()

        else:
            # TODO need to know how many keys there are so that we can get the first one
            # so that it matches the initial command key
            lastcmd = argv[-1] if all else argv[-(self.numKeys * 2)]
            schemaname = self.getSchemaCommandNameFromCliName(lastcmd, self.model)
            if schemaname:
                # leaf will gather all the config info for the object
                #l = LeafCmd(schemaname, lastcmd, "show", self, None, [self.model], [self.schema])
                #l.applybaseshow(lastcmd)
                config = None

                if 'objname' in self.schema[schemaname]['properties'] and argv[-1] == lastcmd:
                    config = CmdEntry(self, self.schema[schemaname]['properties']['objname']['default'], {})
                    config.setValid(True)
                    self.configList.append(config)


                if not config:
                    # only display the what is available from this object
                    for k, v in self.schema[schemaname]['properties']['commands']['properties'].iteritems():
                        # looping through the subcmds to find one that has an object associated with it.
                        if type(v) in (dict, jsonref.JsonRef):
                            if "objname" in v.keys():
                                # each subcmd will either be a link to another subcommand
                                # or a commands containing attributes of an object, which should hold
                                # the object in question associated with this command.

                                listAttrs = self.model[schemaname]['listattrs'] if 'listattrs' in self.model[schemaname] else []

                                allCmdsList = self.prepareConfigTreeObjects(None,
                                                    schemaname,
                                                    False,
                                                    self.model[schemaname]['cliname'],
                                                    self.model[schemaname]["commands"],
                                                    self.schema[schemaname]["properties"]["commands"]["properties"],
                                                    listAttrs)

                                # lets fill out the object to attributes mapping valid for this level in the tree
                                self.objDict = createChildTreeObjectsDict(allCmdsList)
                                configObj = self
                                if configObj:
                                    # TODO need to be able to handle multiple keys
                                    # get the current leaf container key value
                                    keyvalueDict = {}
                                    # only care about command indexes
                                    numKeys = [x for x in range(1, (self.numKeys*2)+1) if x % 2 == 0]
                                    numKeys.reverse()
                                    # lets record the command
                                    for i in numKeys:
                                        keyvalueDict.update({argv[-i]: argv[-(i-1)]})

                                    # lets go through the valid sub tree command objects
                                    # and fill in what command was entered by the user
                                    for objname, objattrs in self.objDict.iteritems():

                                        config = CmdEntry(self, objname, self.objDict[objname])
                                        # total keys must be provisioned for config to be valid
                                        # the keyvalueDict may contain more tree keys than is applicable for the
                                        # config tree
                                        objkeyslen = len([(k, v) for k, v in objattrs.iteritems()
                                                                            if v['isattrkey']])

                                        isvalid = len(keyvalueDict) >= objkeyslen and objkeyslen != 0

                                        isValidKeyConfig = len([(k, v) for k, v in objattrs.iteritems() if v['isattrkey']
                                                                                     and (k in keyvalueDict)]) > 0
                                        # we want a full key config
                                        if isValidKeyConfig:
                                            for basekey, basevalue in keyvalueDict.iteritems():
                                                if basekey in objattrs:
                                                    # all keys for an object must be set and
                                                    # and all all attributes must have default values
                                                    # in order for the object to be considered valid and
                                                    # ready to be provisioned.
                                                    config.setValid(isvalid)
                                                    # no was stripped before
                                                    config.set(argv, False, basekey, basevalue, isKey=objattrs[basekey]['isattrkey'], isattrlist=objattrs[basekey]['isarray'])

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

                                    #config = CmdEntry(self, v['objname']['default'], slf.objDict)
                                    #config.setValid(True)
                                    #self.configList.append(config)



                self.show_state(all=all)
                self.configList.remove(config)

    def get_sdk_func_key_values(self, data, func):
        """
        Get the arguments for the REST api calls
        :param data:
        :param func:
        :return:
        """
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
        """
        Make the REST api call
        :param all:
        :return:
        """
        showObj = self.getShowObj()
        if showObj and showObj.configList:
            sys.stdout.write("Applying Show:\n")

            # tell the user what attributes are being applied
            for i in range(len(showObj.configList)):
                config = showObj.configList[-(i+1)]
                #config.show()

                # get the sdk
                sdk = self.getSdkShow()
                #funcObjName = config.name + 's' if 'State' in config.name else config.name + 'States'
                funcObjName = config.name
                try:
                    if all:
                        funclower = funcObjName.lower()
                        if funclower in self.schema and self.schema[funclower]['properties'].has_key('useCombinedPrintFn'):
                            printall_func = getattr(sdk, 'printCombined' + funcObjName + 's')
                        else:
                            printall_func = getattr(sdk, 'print' + funcObjName + 's')
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
