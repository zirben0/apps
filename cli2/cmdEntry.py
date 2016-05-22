#!/usr/lib/python
# object which stores the current configuration
import sys
import copy
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

def getEntryAttribute(entry):
    return entry.attr

def getEntryValue(entry):
    return entry.val

def getEntryCmd(entry):
    return entry.cmd

def getEntrytime(entry):
    return entry.date

class CmdSet(object):

    def __init__(self, cmd, attr, val):
        self.cmd = cmd
        self.attr = attr
        self.val = val
        self.date = time.ctime()

    def set(self, val):
        self.val = val
        self.date = time.ctime()

class CmdEntry(object):

    def __init__(self, name, keyDict):
        # used to determine if this is a config object
        # which is marked for config
        # some cnfig key attributes are set across configs
        # so this flag will allow config obj to know
        # to send this config to hw
        self.valid = False
        # holds the name of the object
        self.name = name
        # hold provisioned values
        # { 'configcmd': string
        #   'attr' : { attr:value }}
        self.attrList = []
        # holds the attributes which are keys to this config object
        # initially holds default values
        # { cliname : {'modelname' : name,
        #              'value' : value} }
        self.keysDict = copy.deepcopy(keyDict)

    def isValid(self):
        return self.valid

    def setValid(self, v):
        self.valid = v

    def set(self, fullcmd, k, v):
        for entry in self.attrList:
            if getEntryAttribute(entry) == k:
                entry.set(v)
                return

        self.attrList.append(CmdSet(' '.join(fullcmd),k, v))

    def clear(self, k=None, v=None, all=None):
        try:
            if not all:
                delcmd = None
                for entry in self.attrList:
                    if k == self.getEntryAttribute(entry):
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

    def getSdkConfig(self):
        newdict = {}
        for entry in self.getallconfig():
            for kk, vv in copy.deepcopy(self.keysDict).iteritems():
                if kk == getEntryAttribute(entry):
                    # overwrite the default value
                    value = None
                    if self.keysDict[kk]['isarray']:
                        if isnumeric(self.keysDict[kk]['type']):
                            l = [x.lstrip('').rstrip('') for x in getEntryValue(entry).split(",")]
                            value = [int(x) for x in l]
                        elif isboolean(self.keysDict[kk]['type']):
                            l = [x.lstrip('').rstrip('') for x in getEntryValue(entry).split(",")]
                            value = [convertStrBoolToBool(x) for x in l]
                        else:
                            value = [x.lstrip('').rstrip('') for x in getEntryValue(entry).split(",")]

                    else:
                        if isnumeric(self.keysDict[kk]['type']):
                            value = int(getEntryValue(entry))
                        elif isboolean(self.keysDict[kk]['type']):
                            value = convertStrBoolToBool(getEntryValue(entry))
                        else:
                            self.keysDict[kk].update({'value': getEntryValue(entry)})
                            newdict.update({vv['key']: getEntryValue(entry)})

                    self.keysDict[kk].update({'value': value})
                    newdict.update({vv['key']: value})

        # lets add the rest of the attributes that are part of this
        # config object
        for k, v in self.keysDict.iteritems():
            if v['key'] not in newdict:
                if v['isarray']:
                    v['value'] = []
                newdict.update({v['key']: v['value']})

        return newdict

    def applyconfig(self):
        pass

    def show(self):
        #sys.stdout.write("objkey: \n")
        keystr = ''
        #for k, v in self.keysDict.iteritems():
        #    if v['value'] is not None:
        #        sys.stdout.write("%s:%s \n" %(k, v['value']))

        #sys.stdout.write('\n%s\n' %(keystr))

        sys.stdout.write('\tobject: %s\n' %(self.name))

        labels = ('command', 'attr', 'value', 'time provisioned')
        rows = []
        for entry in self.attrList:
            rows.append((getEntryCmd(entry), getEntryAttribute(entry), getEntryValue(entry), getEntrytime(entry)))
        width = 30
        print indent([labels]+rows, hasHeader=True, separateRows=False,
                     prefix=' ', postfix=' ', headerChar= '-', delim='    ',
                     wrapfunc=lambda x: wrap_onspace_strict(x,width))
