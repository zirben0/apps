import os
import sys
import time
import argparse
import shutil
import threading
import json
import requests

headers = {'Accept' : 'application/json', 'Content-Type' : 'application/json'}
httpSuccessCodes = [200, 201, 202, 204]
def runIfSystemIsReady(method):
    def runMethod(self, *args, **kwargs):
        stateUrlBase = 'http://%s:%s/public/v1/state/'%(self.ip, str(self.port))
        reqUrl = stateUrlBase+'SystemStatus'
        while True:
            r = requests.get(reqUrl, data=json.dumps({}), headers=headers)
            if r.status_code in httpSuccessCodes:
                resp = r.json()
                if resp['Object']['Ready'] == True:
                    return method(self, *args, **kwargs)
            time.sleep(1)
    return runMethod

class ConfigMonitor(object):
    def __init__(self, ip, port, cfgDir, pollFreq=5):
        self.ip = ip
        self.port = port
        self.cfgDir = cfgDir
        self.runningCfg = cfgDir + '/runningConfig.json'
        self.desiredCfg = cfgDir + '/desiredConfig.json'
        self.apiBase = 'http://%s:%s/public/v1/'%(self.ip, str(self.port))

    @runIfSystemIsReady
    def applyDesiredConfig(self):
        with open(self.desiredCfg) as cfgFile:
            configData = json.load(cfgFile)
            r = requests.post(self.apiBase+'action/ForceApplyConfig', data=json.dumps(configData), headers=headers)
            if r.status_code in httpSuccessCodes:
                print 'Configuration Applied from file %s'  %(monitor.runningCfg)
            else:
                print 'Failed to apply configuration:  %s'  %(r.text)

    @runIfSystemIsReady
    def saveConfig(self):
        cfgData = {'FileName': self.runningCfg}
        r = requests.post(self.apiBase+'action/SaveConfig', data=json.dumps(cfgData), headers=headers)
        if r.status_code in httpSuccessCodes:
            print 'Configuration is saved to %s'  %(monitor.runningCfg)
        else:
            print 'Saving Configuration failed: %s'  %(r.text)


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

    parser.add_argument('--applyConfig',
                        type=bool,
                        dest='applyConfig',
                        action='store',
                        nargs='?',
                        default=False,
                        help='Apply Configuration')

    parser.add_argument('--saveConfig',
                        type=bool,
                        dest='saveConfig',
                        action='store',
                        nargs='?',
                        default=False,
                        help='Save Configuration')
    args = parser.parse_args()

    if ((args.saveConfig == False and args.applyConfig == False) or
        (args.saveConfig == True and args.applyConfig == True)):
        parser.print_usage()
        sys.exit(1)

    monitor = ConfigMonitor(args.ip, args.port, args.cfgDir)
    if args.saveConfig != False:
        monitor.saveConfig()

    if args.applyConfig != False:
        monitor.applyDesiredConfig()
