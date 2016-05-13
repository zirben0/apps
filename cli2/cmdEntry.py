#!/usr/lib/python
# object which stores the current configuration
import sys

class CmdEntry(object):

    attrDict = {}
    funcDict = {}
    def __init__(self, name, keyDict):
        # holds the name of the object
        self.name = name
        # holds the attributes which are keys to this config object
        # { cliname : {'modelname' : name,
        #              'value' : value} }
        self.keysDict = keyDict

    def set(self, k, v):
        self.attrDict.update({k:v})

    def clear(self, k, v, all=None):
        try:
            if not all:
                del(self.attrDict, k)
            else:
                self.attrDict = {}
        except Exception:
            pass

    def getall(self, ):
        return self.attrDict

    def setcallmethod(self, prefix, func):
        self.funcDict.update({prefix, func})

    def applyconfig(self):
        pass

    def show(self):
        sys.stdout.write("objkey: ")
        keystr = ''
        for k, v in self.keysDict.iteritems():
            keystr += "%s:%s " %(k, v['value'])
        sys.stdout.write('%s' %(keystr))
        for k, v in self.attrDict.iteritems():
            sys.stdout.write("%s: %s\n" %(k, v))

