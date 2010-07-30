'''
Created on Jul 20, 2010

@author: ghoti
'''
import logging
import database
import ConfigParser
import os

config = ConfigParser.ConfigParser()
config.readfp(open(os.path.abspath('.') + '/config.cfg'))
output = logging.getLogger('monitor.events')
output.setLevel(int(config.get('console', 'level')))
db = database.Database()
'''
PunkBuster Server: New Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) \[(?P<something>[^\s]+)\]\s"(?P<name>.+)".*$')
'''              
def PBNewConnection(players, data):
    console.debug(data.groups())
    p = players.getplayer(data.group('name'))
    if p is None:
        players.connect(data.group('name'))
        p = players.getplayer(data.group('name'))
    p.ip = data.group('ip')

'''
PunkBuster Server: Lost Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) (?P<pbuid>[^\s]+)\(-\)\s(?P<name>.+)$'
'''  
def PBLostConnection(players, data):
    console.debug(data.groups())
    p = players.getplayer(data.group('name'))
    if p is not None:
        players.disconnect(data.group('name'))

'''
PunkBuster Server: Running PB Scheduled Task \(slot #(?P<slot>\d+)\)\s+(?P<task>.*)$
'''
def PBScheduledTask(players, data):
    console.debug(data.groups())
    
'''
PunkBuster Server: Player GUID Computed (?P<pbid>[0-9a-fA-F]+)\(-\) \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+)\s(?P<name>.+)$
'''
def PBPlayerGuid(players, data):
    console.debug(data.groups())
    p = players.getplayer(data.group('name'))
    if p is None:
        players.connect(data[0])
        p = players.getplayer(data[0])
    p.pbid = data.group('pbid')
    p.id = data.group('ip')
    db.write_player(p)

'''
PunkBuster Server: Master Query Sent to \((?P<pbmaster>[^\s]+)\) (?P<ip>[^:]+)$
'''
def PBMasterQuerySent(players, data):
    console.debug(data.groups())