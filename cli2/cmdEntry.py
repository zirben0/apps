#!/usr/lib/python
# object which stores the current configuration
import sys
import copy

class CmdEntry(object):


    def __init__(self, name, keyDict):
        # holds the name of the object
        self.name = name
        # hold provisioned values
        self.attrDict = {}
        # holds the attributes which are keys to this config object
        # { cliname : {'modelname' : name,
        #              'value' : value} }
        self.keysDict = copy.deepcopy(keyDict)

    def set(self, k, v):
        self.attrDict.update({k:v})

    def clear(self, k, v, all=None):
        try:
            if not all:
                del(self.attrDict, k)
                if k in self.keysDict:
                    del(self.keysDict, k)
            else:
                self.attrDict = {}
                self.keysDict = {}
        except Exception:
            pass

    def getall(self, ):
        return self.attrDict

    def getSdkAll(self):
        newdict = {}
        for k, v in self.getall().iteritems():
            for kk, vv in copy.deepcopy(self.keysDict).iteritems():
                if k == kk:
                    newdict.update({vv['key']: v})
                    self.keysDict[kk].update({'value': v})
        return newdict

    def applyconfig(self):
        pass

    def show(self):
        #sys.stdout.write("objkey: \n")
        keystr = ''
        for k, v in self.keysDict.iteritems():
            if v['value'] is not None:
                sys.stdout.write("%s:%s \n" %(k, v['value']))

        #sys.stdout.write('\n%s\n' %(keystr))
        sys.stdout.write("objname[%s]:\n" %(self.name))
        for k, v in self.attrDict.iteritems():
            sys.stdout.write("\t%s: %s\n" %(self.name, k, v))

