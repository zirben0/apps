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
#

import string
import sys
from cmdEntry import CmdSet

COMMAND_TYPE_DELETE = 'delete'
COMMAND_TYPE_CONFIG = 'config'
COMMAND_TYPE_SHOW = 'show'
COMMAND_TYPE_CONFIG_NOW = 'now'
COMMAND_TYPE_INIT = 'init'

# these model attribute names will possibly have the cliname changed within the cli
# model to a name picked by asicd.conf to represent a port
DYNAMIC_MODEL_ATTR_NAME_LIST = ('IntfRef', 'IfIndex', 'Port', 'Members', 'IntfList', 'UntagIntfList', 'PhysicalPort', 'AddressLessIf')

# lets keep track of the various two value names that might not need to be represented in the cli
CLI_COMMAND_POSITIVE_TRUTH_VALUES = ('true', 'on', 'up', True)
CLI_COMMAND_NEGATIVE_TRUTH_VALUES = ('false', 'off', 'down', False)

PORT_NAME_PREFIX = 'ethernet'

# helper functions
def isnumeric(v):
    return v in ('int', 'uint', 'uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32')

def isboolean(v):
    return v and v.lower() in ('bool', 'boolean')

def convertStrBoolToBool(v):
    if v and str(v).lower() in ('true', '1'):
        return True
    elif v and type(v) is bool:
        return v
    return False

def convertStrNumToNum(v):
    val = v
    try:
        if isinstance(v, unicode):
            val = string.atoi(v.decode('ascii'))
        elif isinstance(v, str):
            val =string.atoi(v)
    except Exception:
        val = 0
    return val

def updateSpecialValueCases(cfgobj, k, v):
    '''
    This function is meant to handle special cases where we need to convert the value to some special
    value.  Not sure if this is the correct place to handle this but since it is only once case
    going to perform the operation here.
    :param k: Model name of attribute
    :param v: CmdSet
    :return:
    '''
    tmpval = v.val if type(v) == CmdSet else v
    if k in DYNAMIC_MODEL_ATTR_NAME_LIST:

        if type(v) == CmdSet:
            if type(v.val) is list:
                tmpvallist = []
                for value in v.val:
                    if "/" in str(value):
                        value = v.attr + str(value).split('/')[1]
                    elif v.attr not in str(value):
                        value = v.attr + str(value)
                    tmpvallist.append(str(value))
                tmpval = tmpvallist
            else:
                if "/" in str(v.val):
                    v.val = v.attr + v.val.split('/')[1]
                elif v.attr not in str(v.val):
                    v.val = v.attr + str(v.val)
                tmpval = str(v.val)

        # cli always expects the string name, but lets
        # convert the string name to the number
        if k in ('IfIndex', 'Members'):
            # Port object is gathered on cli start
            if type(tmpval) is list:
                ifindexList = []
                for tmpv in tmpval:
                    value = cfgobj.getIntfRefToIfIndex(tmpv)
                    if value is not None:
                        ifindexList.append(value)

                tmpval = ifindexList
                '''
                Not handling this case as don't see a need
                else:
                    # if we reached here the other options for IfIndex are
                    # 1) Vlan
                    # 2) Lag

                    # lets try a vlan interface
                    sdk = self.cfgobj.getSdk()
                    vlans = sdk.getAllVlanStates()
                    for vlan in vlans:
                        v = vlan['Object']
                        if v['VlanName'] == tmpval:
                            value = v['IfIndex']

                    if value is None:
                        vlans = sdk.getAllLaPortChannelStates()
                        for vlan in vlans:
                            v = vlan['Object']
                            if v['Name'] == tmpval:
                                value = v['IfIndex']

                    if value is not None:
                        tmpval = value
                '''

            else:
                value = cfgobj.getIntfRefToIfIndex(tmpval)
                if value is not None:
                    tmpval = value
                else:
                    # if we reached here the other options for IfIndex are
                    # 1) Vlan
                    # 2) Lag

                    # lets try a vlan interface
                    sdk = cfgobj.getSdk()
                    vlans = sdk.getAllVlanStates()
                    for vlan in vlans:
                        v = vlan['Object']
                        if v['VlanName'] == tmpval:
                            value = v['IfIndex']

                    if value is None:
                        vlans = sdk.getAllLaPortChannelStates()
                        for vlan in vlans:
                            v = vlan['Object']
                            if v['Name'] == tmpval:
                                value = v['IfIndex']

                    if value is not None:
                        tmpval = value

    return tmpval


def printErrorValueCmd(i, mline):
    lenstr = len(" ".join(mline[:-1]))
    sys.stdout.write("%s\n" %(" ".join(mline)))
    spaces = " " * lenstr
    sys.stdout.write("%s\n" %(spaces + " ^"))

# model macros
def GET_MODEL_COMMANDS(schemaname, model):
    return model[schemaname]["commands"] if schemaname in model else model["commands"]

def GET_SCHEMA_COMMANDS(schemaname, schema):
    return schema[schemaname]["properties"]["commands"]["properties"] if schemaname in schema else schema["properties"]["commands"]["properties"]

def getValueInSchema(schema):
    '''
    Value contains the keys for a given model object
    :param schema:
    :return:
    '''
    if "properties" in schema and \
            "value" in schema["properties"] and \
            'properties' in schema['properties']['value']:
        return schema['properties']['value']['properties']
    return None

def getValueArgumentType(attrdata):
    if 'properties' in attrdata and 'argtype' in attrdata['properties'] and 'type' in attrdata['properties']['argtype']:
        return attrdata['properties']['argtype']['type']
    return None

def isValueArgumentList(attrdata):
    if 'properties' in attrdata and 'islist' in attrdata['properties'] and 'default' in attrdata['properties']['islist']:
        return attrdata['properties']['islist']['default']
    return False


def getValueArgumentSelections(attrdata):
    if 'properties' in attrdata and 'argtype' in attrdata['properties'] and 'enum' in attrdata['properties']['argtype']:
        return attrdata['properties']['argtype']['enum']
    return None

def isSelectionTypeNotNeeded(selections, argtype):
    '''
    If selection is only two values and these values are represented as
    a value which is basically like enable/disable on/off... then no
    value is needed by the user, they simply just need to enter the
    attribute to set, and no attribute to unset
    :param selections:
    :param attrtype:
    :return:
    '''
    return len(selections) == 2 and \
                (not isboolean(argtype) and
                    not isnumeric(argtype)
                        and len(frozenset(CLI_COMMAND_NEGATIVE_TRUTH_VALUES +
                                          CLI_COMMAND_POSITIVE_TRUTH_VALUES).intersection([str(x).lower() for x in selections])) == 2)


def getSchemaObjName(schemaname, schema):
    return schema[schemaname]['properties']['objname']['default']

def getHelp(schemaname, model, schema):
    if 'help' in model[schemaname]:
        return model[schemaname]['help']
    return schema[schemaname]['properties']['help']['default']

def getSchemaCommandAttrDefaultArg(command):
    return command['properties']['defaultarg']['default']

def getSchemaCommandAttrIsDefaultSet(command):
    return command['properties']['isdefaultset']['default']

def getSchemaAttrSelection(value):
    if 'properties' in value and \
            value['properties'] and \
                    'argtype' in value['properties'] and \
                    'enum' in value['properties']['argtype']:
        return value['properties']['argtype']['enum']
    return []

def getSchemaAttrMinMax(value):
    if 'properties' in value and \
            value['properties'] and \
                    'argtype' in value['properties'] and \
                    'minimum' in value['properties']['argtype']:
        return (value['properties']['argtype']['minimum'],value['properties']['argtype']['maximum'])
    return (None, None)

def getAttrHelp(mvalue, svalue):
    if 'help' in mvalue:
        return mvalue['help']
    return svalue['properties']['help']['default']

def getAttrCliName(mvalue, svalue):
    if 'cliname' in mvalue:
        return mvalue['cliname']
    return svalue['properties']['cliname']['default']

