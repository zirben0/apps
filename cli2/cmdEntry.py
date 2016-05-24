#!/usr/lib/python
# object which stores the current configuration
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

    def __init__(self, cmd, delete, attr, val):
        self.cmd = cmd
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

class CmdEntry(object):

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
        # hold provisioned values
        # { 'configcmd': string
        #   'attr' : { attr:value }}
        self.attrList = []
        # holds the attributes which are keys to this config object
        # initially holds default values
        # { cliname : {'modelname' : name,
        #              'value' : value} }
        self.keysDict = copy.deepcopy(keyDict)

    def __str__(self):
        lines = "name: %s\nvalid: %sdelete %s\n" %(self.name, self.valid, self.delete)
        lines += "attrList: %s\n" %(self.attrList)
        lines += "keysDict: %s\n" %(self.keysDict)
        return lines

    def isValid(self):
        return self.valid

    def setValid(self, v):
        self.valid = v

    def setPending(self, p):
        self.pending = p

    def setDelete(self, d):
        self.delete = d

    def set(self, fullcmd, delete, k, v):
        for entry in self.attrList:
            if getEntryAttribute(entry) == k:
                # TODO if delete then we may need to remove this command all together
                entry.set(' '.join(fullcmd), delete, k, v)
                return

        self.attrList.append(CmdSet(' '.join(fullcmd), delete, k, v))

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
                            l = [convertStrNumToNum(x.lstrip('').rstrip('')) for x in getEntryValue(entry).split(",")]
                            value = [int(x) for x in l]
                        elif isboolean(self.keysDict[kk]['type']):
                            l = [convertStrBoolToBool(x.lstrip('').rstrip('')) for x in getEntryValue(entry).split(",")]
                            value = [convertStrBoolToBool(x) for x in l]
                        else:
                            value = [x.lstrip('').rstrip('') for x in getEntryValue(entry).split(",")]

                    else:
                        if isnumeric(self.keysDict[kk]['type']):
                            value = convertStrNumToNum(getEntryValue(entry))
                        elif isboolean(self.keysDict[kk]['type']):
                            value = convertStrBoolToBool(getEntryValue(entry))
                        else:
                            value = getEntryValue(entry)

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
