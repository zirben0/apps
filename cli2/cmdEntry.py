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
# Container classes for cli commands entered from user and also contains default values from model schema,
# ref from model, or values read from reading database when object exists
#
import sys
import copy
import string
from tablePrint import indent, wrap_onspace_strict
import time
ATTRIBUTE = 0
VALUE = 1


def isnumeric(v):
    return v in ('int', 'uint', 'uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32')

def isboolean(v):
    return v.lower() in ('bool', 'boolean')

def convertStrBoolToBool(v):
    if v.lower() in ('true', '1'):
        return True
    return False

def convertStrNumToNum(v):
    try:
        val = string.atoi(v)
    except Exception:
        val = 0
    return val

def getEntryAttribute(entry):
    return entry.attr

def getEntryValue(entry):
    return entry.val

def getEntryCmd(entry):
    return entry.cmd

def getEntrytime(entry):
    return entry.date

class CmdSet(object):
    '''
    Hold the attributes related to a cli command given
    '''
    def __init__(self, cmd, delete, attr, val, iskey):
        self.cmd = cmd
        self.iskey = iskey
        self.delete = delete
        self.attr = attr
        self.val = val
        self.date = time.ctime()

    def __str__(self,):
        lines = "cmd: %s\ndelete %s\n attr %s\n val %s\n date %s\n" %(self.cmd, self.delete, self.attr, self.val, self.date)
        return lines


    def set(self, cmd, delete, attr, val):
        self.cmd = cmd
        self.delete = delete
        self.attr = attr
        self.val = val
        self.date = time.ctime()

    def get(self):
        return (self.cmd, self.attr, self.val)

    def isKey(self):
        return self.val if self.isKey else None

class CmdEntry(object):
    '''

    '''

    def __init__(self, name, keyDict):
        # used to determine if this is a config object
        # which is marked for config
        # some cnfig key attributes are set across configs
        # so this flag will allow config obj to know
        # to send this config to hw
        self.valid = False
        # if the base key command was added
        # then the config may be pending waiting for the
        # second attribute to be set on the object
        self.pending = True
        # This is a delete command, meaning we want to
        # update to a default or delete an object
        self.delete = False
        # holds the name of the object
        self.name = name
        # holds provisioned values from user as a list of CmdSet
        self.attrList = []
        # holds the attributes which are keys to this config object
        # initially holds default values for attributes which are
        # contained in the json schema
        self.keysDict = copy.deepcopy(keyDict)

    def __str__(self):
        lines = "name: %s\nvalid: %sdelete %s\n" %(self.name, self.valid, self.delete)
        lines += "attrList: %s\n" %(self.attrList)
        lines += "keysDict: %s\n" %(self.keysDict)
        return lines

    def isEntryEmpty(self):
        return len(self.attrList) == 0

    def isValid(self):
        return self.valid

    def setValid(self, v):
        self.valid = v

    def setPending(self, p):
        self.pending = p

    def setDelete(self, d):
        self.delete = d

    def updateSpecialValueCases(self, k, v):
        '''
        This function is meant to handle special cases where we need to convert the value to some special
        value.  Not sure if this is the correct place to handle this but since it is only once case
        going to perform the operation here.
        :param k: Model name of attribute
        :param v: CmdSet
        :return:
        '''
        if k in ('IntfRef', 'IfIndex', 'Port'):
            if "/" in v.val:
                v.val = v.attr + v.val.split('/')[1]

        return v

    def set(self, fullcmd, delete, k, v, isKey=False):

        for entry in self.attrList:
            if getEntryAttribute(entry) == k:
                # TODO if delete then we may need to remove this command all together
                entry.set(' '.join(fullcmd), delete, k, v)
                return

        self.attrList.append(CmdSet(' '.join(fullcmd), delete, k, v, isKey))

    def clear(self, k=None, v=None, all=None):
        try:
            if not all:
                delcmd = None
                for entry in self.attrList:
                    if k == getEntryAttribute(entry):
                        delcmd = entry

                if delcmd is not None:
                    self.attrList.remove(delcmd)
            else:
                self.attrList = []
                self.keysDict = {}
        except Exception:
            pass

    def getallconfig(self, ):
        return self.attrList

    def getSdkConfig(self, readdata=None):
        newdict = {}
        for entry in self.getallconfig():
            for kk, vv in copy.deepcopy(self.keysDict).iteritems():
                if kk == getEntryAttribute(entry):
                    # overwrite the default value
                    value = None
                    if self.keysDict[kk]['isarray']:
                        if isnumeric(self.keysDict[kk]['type']):
                            l = [convertStrNumToNum(self.updateSpecialValueCases(vv['key'], x.lstrip('').rstrip(''))) for x in getEntryValue(entry).split(",")]
                            value = [int(x) for x in l]
                        elif isboolean(self.keysDict[kk]['type']):
                            l = [convertStrBoolToBool(self.updateSpecialValueCases(vv['key'], x.lstrip('').rstrip(''))) for x in getEntryValue(entry).split(",")]
                            value = [convertStrBoolToBool(x) for x in l]
                        else:
                            value = [self.updateSpecialValueCases(vv['key'], x.lstrip('').rstrip('')) for x in getEntryValue(entry).split(",")]

                    else:
                        if isnumeric(self.keysDict[kk]['type']):
                            value = convertStrNumToNum(self.updateSpecialValueCases(vv['key'], getEntryValue(entry)))
                        elif isboolean(self.keysDict[kk]['type']):
                            value = convertStrBoolToBool(self.updateSpecialValueCases(vv['key'], getEntryValue(entry)))
                        else:
                            value = getEntryValue(self.updateSpecialValueCases(vv['key'], entry))

                    if readdata:
                        del readdata[vv['key']]

                    #self.keysDict[kk].update({'value': value})
                    newdict.update({vv['key']: value})

        # lets add the defaults for the rest of the attributes that are part of this
        # config object
        for kk, v in self.keysDict.iteritems():
            if v['key'] not in newdict:
                value = None
                if not readdata:
                    if self.keysDict[kk]['isarray']:
                        if isnumeric(self.keysDict[kk]['type']):
                            l = [convertStrNumToNum(x.lstrip('').rstrip('')) for x in v['value'].split(",")]
                            value = [int(x) for x in l]
                        elif isboolean(self.keysDict[kk]['type']):
                            l = [convertStrBoolToBool(x.lstrip('').rstrip('')) for x in v['value'].split(",")]
                            value = [convertStrBoolToBool(x) for x in l]
                        else:
                            value = [x.lstrip('').rstrip('') for x in v['value'].split(",")]
                    else:
                        if isnumeric(self.keysDict[kk]['type']):
                            value = convertStrNumToNum(v['value'])
                        elif isboolean(self.keysDict[kk]['type']):
                            value = convertStrBoolToBool(v['value'])
                        else:
                            value = v['value']
                elif v['key'] in readdata:
                    value = readdata[v['key']]

                newdict.update({v['key']: value})

        return newdict

    def applyconfig(self):
        pass

    def show(self):
        '''
        Display the output of a commands as entered by a user
        :return:
        '''
        sys.stdout.write('\tobject: %s\n' %(self.name))

        labels = ('command', 'attr', 'value', 'time provisioned')
        rows = []
        for entry in self.attrList:
            rows.append((getEntryCmd(entry), getEntryAttribute(entry), getEntryValue(entry), getEntrytime(entry)))
        width = 30
        print indent([labels]+rows, hasHeader=True, separateRows=False,
                     prefix=' ', postfix=' ', headerChar= '-', delim='    ',
                     wrapfunc=lambda x: wrap_onspace_strict(x,width))
