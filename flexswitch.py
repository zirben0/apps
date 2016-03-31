import requests
import json
import urllib2

headers = {'Accept' : 'application/json', 'Content-Type' : 'application/json'}

class FlexSwitch( object):
    def  __init__ (self, ip, port):
        self.ip    = ip
        self.port  = port 
        self.urlBase = 'http://%s:%s/public/v1/'%(ip,str(port))

    def createSVI( self, intfIp, vlanId) :
        obj =  { 'IpAddr'   : intfIp,
                 'IfIndex' : self.getVlanInfo(vlanId),
               }
        reqUrl =  self.urlBase+'IPv4Intf'
        r = requests.post(reqUrl, data=json.dumps(obj), headers=headers)

    def getVlanInfo (self, vlanId) :
        for vlan in self.getObjects ('Vlans'):
            print vlan 
            if vlan['VlanId'] == vlanId:
                return int(vlan['IfIndex'])

    def createVlan (self, vlanId, ports, taggedports):
        obj =  { 'VlanId': int(vlanId),
                 'IfIndexList' : ports,
                 'UntagIfIndexList': taggedports 
               }
        reqUrl =  self.urlBase+'VlanConfig'
        r = requests.post(reqUrl, data=json.dumps(obj), headers=headers)
        return r


    def addPortVlan (self, vlanId, ports, taggedports):
        obj =  { 'VlanId': int(vlanId),
                 'IfIndexList' : ports,
                 'UntagIfIndexList': taggedports 
               }
               
    def createBgpGlobal(self, asnum, rtrid):
        obj =  { 
                'AS'         : asnum,
                'RouterId'   : rtrid,
               }
        reqUrl =  self.urlBase+'BGPGlobalConfig'
        r = requests.post(reqUrl, data=json.dumps(obj), headers=headers)

    def createBgpPeer(self, nbrIp, peeras, localas):
        obj =  { 
                'PeerAS'         : peeras ,
                'LocalAS'        : localas,
                'AuthPassword'   : '',
                'ConnnectRetryTime': 120, 
                'HoldTime'         : 3,
                'KeepaliveTime'    : 1,
                'Description'      : '' ,
                'NeighborAddress' : nbrIp 
               }
        reqUrl =  self.urlBase+'BGPNeighborConfig'
        r = requests.post(reqUrl, data=json.dumps(obj), headers=headers)

    def createOspfGlobal(self, rtrid):
        obj =  { 
                'RouterIdKey' : rtrid,
               }
        reqUrl =  self.urlBase+'OspfGlobalConfig'
        r = requests.post(reqUrl, data=json.dumps(obj), headers=headers)

    def createOspfIntf(self, 
                       ipaddr, 
                       ifIndex = 0,
                       areaId = 0, 
                       ifType = 1,
                       priority = 1,
                       helloIntvl = 10,
                       authKey ='',
                       authType =0
                       ):
        obj =  { 
                'IfIpAddressKey' : ipaddr,
                'AddressLessIfKey' : ifIndex,
                'IfAreaId' : areaId, 
                'IfType' :  ifType, 
                'IfAdminStat' :   1,
                'IfRtrPriority' : priority,
                'IfTransitDelay' : 0,
                'IfRetransInterval' : helloIntvl,
                'IfHelloInterval' :   helloIntvl,
                'IfRtrDeadInterval' : 4*helloIntvl, 
                'IfPollInterval' : 0, 
                'IfAuthKey' : authKey ,
                'IfAuthType' : authType
               }
        reqUrl =  self.urlBase+'OspfIfEntryConfig'
        r = requests.post(reqUrl, data=json.dumps(obj), headers=headers)

    def createRedistributionPolicy(self):
        obj = {"Name"           :"RedistributeConnectedToBGP", 
          "MatchPrefixSet": {"PrefixSet" :"", "MatchSetOptions" : 0}, 
          "InstallProtocolEq":"Connected", 
          "RouteDisposition": "", 
          "Redistribute":True, 
          "RedistributeTargetProtocol":"BGP"}

        reqUrl =  self.urlBase+'PolicyDefinitionStmt'
        r = requests.post(reqUrl, data=json.dumps(obj), headers=headers)

    # configure lag group
    # id - lag id # will be converted to aggId-<id>
    # type - 0 == LACP, 1 == STATIC
    # mode - 0 == ACTIVE, 1 == PASSIVE
    # period - 0 == SLOW, 1 == FAST
    # sysmac - format 'XX:XX:XX:XX:XX:XX'

    def createLag(self, lagId, lagType, sysmac, sysprio, mode, period, hashmode):
        obj = {
            'NameKey' : "aggId-%s" %lagId,
            'LagType' : lagType,
            'Type'    : "ETH",
            'Description' : "Test lag creation",
            'Enabled' : True,
            'Interval' : period,
            'LacpMode' : mode,
            'SystemIdMac' : sysmac,
            'SystemPriority' : sysprio,
            'MinLinks' : 1,
            'LagHash' : hashmode,
            'Mtu' : 1518
        }
        reqUrl =  self.urlBase+'AggregationLacpConfig'
        r = requests.post(reqUrl, data=json.dumps(obj), headers=headers)
        print obj["NameKey"], r.__dict__

    # id - port number will be conververt to fpPort-<id>
    def addPortToLag(self, id, lagid, desc, speed):
        obj = {
            'NameKey' : 'fpPort-%s' % id,
	        'Enabled' : True,
            'Description' : desc,
            'Mtu' : 1518,
	        'Type' : 'ETH',
	        'MacAddress' : '00:11:22:33:44:55',
	        'DuplexMode' : 0,
	        'Auto'       : True,
	        'Speed'      : speed,
	        'EnableFlowControl' : True,
            'AggregateId' : 'aggId-%s' % lagid
        }
        reqUrl =  self.urlBase+'EthernetConfig'
        r = requests.post(reqUrl, data=json.dumps(obj), headers=headers)
        print obj["NameKey"], r.__dict__

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
		
			

if __name__=='__main__':
    pass