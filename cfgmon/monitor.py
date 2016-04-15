import argparse
import simplejson as json
from flexswitchV2 import FlexSwitch

gObjectsInfo =  {}

class ConfigObjList (object):
    def __init__ (self, name, currentList, newList):
        self.name = name
        self.current = currentList
        self.desire  = newList
        self.attrInfo = gObjectsInfo[name]
        self.currentDict = self.convertObjListToDict(currentList)
        self.desiredDict = self.convertObjListToDict(newList)

    def convertObjListToDict (self, objList):
        retDict = {}
        for item in objList:
            keyStr = ''
            for attrName, attrInfo  in self.attrInfo.iteritems():
                if attrInfo['isKey'] == 'true':
                    keyStr = keyStr + attrName+item[attrName] 

            retDict[keyStr] = item
        return retDict

    def applyConfig (self):
        for key, item in self.desiredDict.iteritems():
            if key not in self.currentDict:
                self.createObj()
            else:
                self.updateObj(None)

        for key, item in self.currentDict.iteritems():
            if key not in self.desiredDict:
                self.deleteObj()

    def createObj (self):
        print 'Creating Object %s' %(self.name)

    def deleteObj (self):
        print 'Deleting Object %s' %(self.name)

    def updateObj (self, newAttrDict):
        print 'Updating object %s' %(self.name)

class ConfigMonitor (object) :
    def __init__ (self, ip, port, cfgDir) :
        global gObjectsInfo
        self.cfgDir = cfgDir
        self.runningCfg = cfgDir + '/runningConfig.json'
        self.desiredCfg = cfgDir + '/desiredConfig.json'
        self.oldCfg     = cfgDir + '/oldConfig.json'
        self.ip = ip
        self.port = port
        self.objects =  {}
        self.swtch = FlexSwitch(self.ip, self.port)
        self.currentConfig = {}
        self.cfgObjOrder = []

        with open('modelInfo/genObjectConfig.json') as objInfoFile:    
            self.objects = json.load(objInfoFile)

        for obj in self.objects.keys():
            attrInfoFile = 'modelInfo/%sMembers.json' %(obj)
            with open(attrInfoFile) as hdl : 
                gObjectsInfo[obj] = json.load(hdl)
            
        with open('modelInfo/configOrder.json') as orderInfoFile:    
            orderInfo = json.load(orderInfoFile)
        self.cfgObjOrder = orderInfo['Order']
        self.saveConfig()

    def deleteConfig (self) :
        pass

    def applyRunningConfig (self):
        self.applyConfig(self.currentConfig)

    def applyDesiredConfig(self, configFile=None):
        if configFile == None:
            configFile = self.desiredCfg
        with open(configFile) as desired: 
            desiredCfg = json.load(desired)
        self.applyConfig (desiredCfg)

    def applyConfig (self, config) :
        for obj in self.cfgObjOrder:
            if config.has_key(obj):
                objList = ConfigObjList (obj, self.currentConfig[obj], config[obj])
                objList.applyConfig()
                

    def saveConfig(self) :
        for objName, objInfo  in self.objects.iteritems ():
            if 'w' in objInfo['access'] :
                methodName = 'getAll'+objName+'s'
                method =  getattr(self.swtch, methodName, None)
                if method :
                    cfgList = method()
                    if cfgList != None and len(cfgList) :
                        self.currentConfig [objName] = []
                        for cfg in cfgList: 
                            currentObj = json.loads(json.dumps(cfg['Object']))
                            self.currentConfig[objName].append(currentObj)

        with open(self.runningCfg, 'w') as runningCfg:
            json.dump(self.currentConfig, runningCfg, indent=4, separators=(',', ': '))
            
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FlexSwitch Configuration monitor')
    parser.add_argument('--cfgDir',
                        type=str, 
                        dest='cfgDir',
                        action='store',
                        nargs='?',
                        default='/opt/flexswitch/',
                        help='Location of configuration file')

    parser.add_argument('--ip',
                        type=str, 
                        dest='ip',
                        action='store',
                        nargs='?',
                        default='localhost',
                        help='Ip Address of the node')

    parser.add_argument('--port',
                        type=str, 
                        dest='port',
                        action='store',
                        nargs='?',
                        default='8080',
                        help='Port')

    args = parser.parse_args()
    monitor = ConfigMonitor (args.ip, args.port, args.cfgDir)
    monitor.saveConfig()
    monitor.applyRunningConfig()
