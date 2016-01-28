import requests
import json
import urllib2

headers = {'Accept' : 'application/json', 'Content-Type' : 'application/json'}
class FlexSwitch( object):
    def  __init__ (self, ip, port):
        self.ip    = ip
        self.port  = port 
        self.urlBase = 'http://%s:%s/public/v1/'%(ip,str(port))

    def getObjects(self, objName):
        currentMarker = 0
        nextMarker = 0
        count = 10
        more = True
        entries = []
        while more == True:
            qry = 'http://%s:8080/public/v1/%s?CurrentMarker=%d&NextMarker=%d&Count=%d' %(self.ip, objName, currentMarker, nextMarker, count)
            response = requests.get(qry)
            data = response.json()
            more =  data['MoreExist']
            currentMarker =  data['NextMarker']
            NextMarker    =  data['NextMarker']
            if data['StateObjects'] != None:
                entries.extend(data['StateObjects'])
        return entries 
		
    def getVlanInfo (self, vlanId) :
        for vlan in self.getObjects ('VlanStates'):
            print vlan 
            if vlan['VlanId'] == vlanId:
                return int(vlan['IfIndex'])
			

if __name__=='__main__':
    pass
