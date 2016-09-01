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
# Container classes for cli commands entered from user and also contains default values from model schema,
# ref from model, or values read from reading database when object exists
#
import sys
import copy
import string
from tablePrint import indent, wrap_onspace_strict
import time
import snapcliconst
ATTRIBUTE = 0
VALUE = 1

def getEntryAttribute(entry):
    return entry.attr

def getEntryValue(entry):
    return "%s" % entry.val

def getDictEntryValue(entry, attrDict):
    rval = {}
    if type(entry.val) is list:
        rvallist = []
        for subval in entry.val:
            for key, val in subval.iteritems():
                newKey = attrDict[key]['key']
                rval.update({newKey: val})
            rvallist.append(rval)
        return rvallist
    else:
        for key, val in entry.val.iteritems():
            newKey = attrDict[key]['key']
            rval = {newKey: val}
            return rval

def getEntryCmd(entry):
    return entry.cmd

def getEntrytime(entry):
    return entry.date

class CmdSet(object):
    '''
    Hold the attributes related to a cli command given
    '''
    def __init__(self, cmd, delete, attr, val, iskey, islist):
        self.cmd = cmd
        self.iskey = iskey
        self.islist = islist
        self.delete = delete
        self.attr = attr
        self.val = [val] if type(val) is not list and self.islist else val
        self.date = time.ctime()

    def __str__(self,):
        lines = "cmd: %s\niskey %s\ndelete %s\nattr %s\nval %s\ndate %s\n" %(self.cmd, self.iskey, self.delete, self.attr, self.val, self.date)
        return lines

    def setDict(self, cmd, delete, attr, data):
        self.cmd = cmd
        self.delete = delete
        self.attr = attr
        if self.islist:
            delIdx = -1
            for i, v in enumerate(self.val):
                if v[attr] == data[attr]:
                    delIdx = i

            if delIdx != -1:
                del self.val[delIdx]
            self.val.append(data)
        else:
            self.val = data
        self.date = time.ctime()

    def set(self, cmd, delete, attr, val):
        if type(val) == dict:
            self.setDict(cmd, delete, attr, val)
            return
        self.delete = delete
        self.attr = attr
        if self.islist:
            if type(val) is list:
                if self.delete:
                    cmdList = self.cmd.split(',')
                    for cmd, v in zip(copy.deepcopy(cmdList), val):
                        try:
                            self.val.remove(v)
                            cmdList.remove(cmd)
                        except ValueError:
                            pass
                    self.cmd = ",".join(cmdList)
                else:
                    self.cmd += "," + cmd
                    self.val += val
            else:
                if self.delete:
                    cmdList = self.cmd.split(',')
                    try:
                        self.val.remove(val)
                        cmdList .remove(cmd)
                    except ValueError:
                        pass
                    self.cmd = ",".join(cmdList)
                else:
                    self.cmd += "," + cmd
                    self.val.append(val)

        else:
            self.cmd = cmd
            self.val = val
        self.date = time.ctime()

    def get(self):
        return (self.cmd, self.attr, self.val)

    def isKey(self):
        return self.iskey

    def isList(self):
        return self.islist

class CmdEntry(object):
    '''

    '''

    def __init__(self, cfgobj, name, keyDict):
        # reference to the cfg obj
        self.cfgobj = cfgobj
        # used to determine if this is a config object
        # which is marked for config
        # some cnfig key attributes are set across configs
        # so this flag will allow config obj to know
        # to send this config to hw
        self.valid = False
        # Used to determine if the configuration is pending
        # or not. Once applied then should clear everything
        # that is not a key.
        self.pending = True
        # This is a delete command, meaning we want to
        # update to a default or delete an object
        self.delete = False
        # holds the name of the object, plus key attributes
        self.name = name
        # holds the name of hte object
        self.objname = name.split(",")[0]

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

    def isPending(self):
        return self.pending

    def getObjName(self):

        self.name

    def setValid(self, v):
        self.valid = v

    def setPending(self, p):
        self.pending = p

        #TODO should we clear out existing applied config, and leave the key, does not hurt
        # if attributes are still available cause you can update them if they change

    def setDelete(self, d):
        self.delete = d

    def isAttrSet(self, attr):

        for entry in self.attrList:
            if getEntryAttribute(entry) == attr:
                return True
        return False

    def set(self, fullcmd, delete, k, v, isKey=False, isattrlist=False):
        for entry in self.attrList:
            if getEntryAttribute(entry) == k:
                if entry.iskey == True:
                    # not reason to update keys
                    return
                # TODO if delete then we may need to remove this command all together
                # HACK: should fix higher layers to pass in correct values for now
                # key is only set when config is initially created, so if attr is updated
                # then we don't want to overwrite it
                entry.set(' '.join(fullcmd), delete, k, v)
                self.setPending(True)
                return

        self.setPending(True)
        self.attrList.append(CmdSet(' '.join(fullcmd), delete, k, v, isKey, isattrlist))

    def setDict(self, fullcmd, delete, k, v, isKey=False, isattrlist=False):
        for entry in self.attrList:
            if getEntryAttribute(entry) == k:
                # TODO if delete then we may need to remove this command all together
                entry.set(' '.join(fullcmd), delete, k, v)
                return

        self.attrList.append(CmdSet(' '.join(fullcmd), delete, k, v, isKey, isattrlist))

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

    def getSdkConfig(self, readdata=None, rollback=False):
        '''
        Function gets all the arguements need by the flexsdk call
        :param readdata:
        :param defaultonly:
        :return:
        '''
        def handleListUpdate(attrtype, olddata, newdata):
            # found that if user replys with None
            # that this can be bad so lets make sure to
            # check that old data is actually a list
            updatelist = copy.deepcopy(olddata) if type(olddata) is list else []
            for nd in newdata:
                if snapcliconst.isnumeric(attrtype):
                    # if attribute is supplied and it already exists assume delete
                    if nd in olddata:
                        updatelist.remove(nd)
                    else:
                        updatelist.append(nd)

                elif snapcliconst.isnumeric(attrtype):
                    pass
                elif attrtype in ('str', 'string'):
                    # if attribute is supplied and it already exists assume delete
                    if nd in olddata:
                        updatelist.remove(nd)
                    else:
                        updatelist.append(nd)

                else: # struct
                    for od in olddata:
                        deleteupdate = False
                        for key,value in nd:
                            # find a key that matches and that the nd value is not zero, empty string as these are usually
                            # defaults
                            if key in od and od[key] and od[key] == value:
                                deleteupdate = True

                        if deleteupdate:
                            updatelist.remove(nd)
                        else:
                            updatelist.append(nd)
            return updatelist

        newdict = {}
        if not rollback:
            for entry in self.getallconfig():
                for kk, vv in copy.deepcopy(self.keysDict).iteritems():
                    if kk == getEntryAttribute(entry):
                        # overwrite the default value
                        attrtype =  self.keysDict[kk]['type']['type'] if type(self.keysDict[kk]['type']) == dict else self.keysDict[kk]['type']
                        if self.keysDict[kk]['isarray']:
                            if snapcliconst.isnumeric(attrtype):
                                value = snapcliconst.convertStrNumToNum(snapcliconst.updateSpecialValueCases(self.cfgobj, vv['key'], entry))
                            elif snapcliconst.isboolean(attrtype):
                                value = snapcliconst.convertStrNumToNum(snapcliconst.updateSpecialValueCases(self.cfgobj, vv['key'], entry))
                            elif attrtype in ('str', 'string'):
                                value = snapcliconst.updateSpecialValueCases(self.cfgobj, vv['key'], entry)
                            else: # struct
                                value = getDictEntryValue(entry, vv['value'][0])

                            if readdata:
                                value = handleListUpdate(attrtype, readdata[vv['key']], value)
                        else:
                            if snapcliconst.isnumeric(attrtype):
                                value = snapcliconst.convertStrNumToNum(snapcliconst.updateSpecialValueCases(self.cfgobj, vv['key'], entry))
                            elif snapcliconst.isboolean(attrtype):
                                value = snapcliconst.convertStrBoolToBool(snapcliconst.updateSpecialValueCases(self.cfgobj, vv['key'], entry))
                            elif attrtype in ('str', 'string'):
                                value = snapcliconst.updateSpecialValueCases(self.cfgobj, vv['key'], entry)
                            else:
                                value = getDictEntryValue(entry, vv['value'][0])

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
                    attrtype =  self.keysDict[kk]['type']['type'] if type(self.keysDict[kk]['type']) == dict else self.keysDict[kk]['type']

                    if self.keysDict[kk]['isarray']:
                        if snapcliconst.isnumeric(attrtype):
                            l = [snapcliconst.convertStrNumToNum(x.lstrip('').rstrip('')) for x in v['value']['default'].split(",")]
                            value = [int(x) for x in l]
                        elif snapcliconst.isboolean(attrtype):
                            l = [snapcliconst.convertStrBoolToBool(x.lstrip('').rstrip('')) for x in v['value']['default'].split(",")]
                            value = [snapcliconst.convertStrBoolToBool(x) for x in l]
                        elif attrtype in ('str', 'string'):
                            value = [x.lstrip('').rstrip('') for x in v['value']['default'].split(",")]
                            if len(value) == 1 and value[0] == "":
                                value = []
                        else:
                            value = {}
                            for vv in v['value'][0].values():
                                value.update({vv['key'] : vv['value']['default']})
                            value = [value]
                    else:
                        if snapcliconst.isnumeric(attrtype):
                            value = snapcliconst.convertStrNumToNum(v['value']['default'])
                        elif snapcliconst.isboolean(attrtype):
                            value = snapcliconst.convertStrBoolToBool(v['value']['default'])
                        elif attrtype in ('str', 'string'):
                            value = v['value']['default']
                        else:
                            value = {}
                            if type(v['value']) is list and len(v['value']):
                                for vv in v['value'][0].values():
                                    value.update({vv['key'] : vv['value']['default']})
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
        pending = 'PENDING CONFIG'
        if not self.isPending():
            pending = 'APPLIED CONFIG'

        sys.stdout.write('\tobject: %s   status: %s  valid: %s\n' %(self.objname, pending, self.valid))

        labels = ('command', 'attr', 'value', 'iskey', 'time provisioned')
        rows = []
        for entry in self.attrList:
            rows.append((getEntryCmd(entry), getEntryAttribute(entry), getEntryValue(entry), "%s" %(entry.iskey), getEntrytime(entry)))
        width = 30
        print indent([labels]+rows, hasHeader=True, separateRows=False,
                     prefix=' ', postfix=' ', headerChar= '-', delim='    ',
                     wrapfunc=lambda x: wrap_onspace_strict(x, width))
