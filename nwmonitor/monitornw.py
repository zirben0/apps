#!/usr/bin/python
import time
import argparse
from flexswitchV2 import FlexSwitch
class PortStat (object):
    def __init__ (self):
        self.discardCount = 0
        self.discardHistory = [] 

    def updateDiscardCounts (self, count):
        if len(self.discardHistory) < 4:
            self.discardHistory.insert(0, count)
        else:
            self.discardHistory.pop()
            self.discardHistory.insert(0, count)

    def getDiscardRate (self, interval):
        if (len (self.discardHistory) > 1): 
            return (self.discardHistory[0] - self.discardHistory[1])/interval
        else :
            return 0
        

      
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='FlexSwitch Network Monitor')
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
    
    restIf = FlexSwitch(args.ip, args.port)
    portDict = {}
    while True:
        portsInfo = restIf.getAllPortStates()
        for port in portsInfo:
            portName = port['Object']['Name']
            portStat = portDict.get(port['Object']['Name'],None)
            if portStat == None:
                portStat =  PortStat()
                portDict[port['Object']['Name']] = portStat

            portStat.updateDiscardCounts(port['Object']['IfInDiscards'])
            discardRate = portStat.getDiscardRate(5) 
            if port['Object']['IfInDiscards']:
                print 'Port %s Discard Count %s ' %(portName, port['Object']['IfInDiscards'])

            if discardRate > 100:
                print 'Shutting Port %s Discard rate is %s' %(portName, discardRate)
                restIf.updatePort(portName, AdminState= "DOWN")
            else :
                if discardRate > 0:
                    print 'Port %s Discard rate is %s' %(portName, discardRate)
                
            #print '%s : %s ' %(port['Object']['Name'], port['Object']['IfInDiscards'])
            #import ipdb;ipdb.set_trace()
            #if port['Object']['IfInDiscards'] > 0:
            #    print 'ERROR'
            #    print 'Discards exist for %s' %(port['Object']['Name'])
        
        time.sleep(5)
