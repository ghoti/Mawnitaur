'''
Created on Jul 19, 2010

@author: ghoti
'''
from __future__ import with_statement
import logging
import re

import punkbuster
import command

console = logging.getLogger('monitor.events')

kickwords = []
banwords = []

with open('kickwords.txt', 'r') as f:
    for line in f:
        kickwords.append(line.strip('\n'))
        
with open('banwords.txt', 'r') as f:
    for line in f:
        banwords.append(line.strip('\n'))

PBMessages = (
            (re.compile(r'^PunkBuster Server: Running PB Scheduled Task \(slot #(?P<slot>\d+)\)\s+(?P<task>.*)$'), 'PBScheduledTask'),
            (re.compile(r'^PunkBuster Server: Lost Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) (?P<pbuid>[^\s]+)\(-\)\s(?P<name>.+)$'), 'PBLostConnection'),
            (re.compile(r'^PunkBuster Server: Master Query Sent to \((?P<pbmaster>[^\s]+)\) (?P<ip>[^:]+)$'), 'PBMasterQuerySent'),
            (re.compile(r'^PunkBuster Server: Player GUID Computed (?P<pbid>[0-9a-fA-F]+)\(-\) \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+)\s(?P<name>.+)$'), 'PBPlayerGuid'),
            (re.compile(r'^PunkBuster Server: New Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) \[(?P<something>[^\s]+)\]\s"(?P<name>.+)".*$'), 'PBNewConnection')
            )

def onPlayerJoin(players, data):
    console.debug('%s connected' % data[0])
    players.connect(data[0])

#player.onAuthenticated <soldier name: string> <player GUID: guid>
def onPlayerAuthenticated(players, data):
    console.debug('%s received ea_guid' % data[0])
    p = players.getplayer(data[0])
    if p is None:
        players.connect(data[0])
    p.eaid = data[1]
        
def onPlayerLeave(players, data):
    console.debug('%s left' % data[0])
    p = players.getplayer(data[0])
    if p is not None:
        players.disconnect(data[0])
        
def onPlayerKill(players, data):
    console.debug('%s killed %s' % (data[0], data[1]))
    attacker = players.getplayer(data[0])
    weapon = data[2]
    headshot = data[3]
    
    if attacker is None:
        players.connect(data[0])
        attacker = players.getplayer(data[0])
    victim = players.getplayer(data[1])
    if victim is None:
        players.connect(data[1])
        victim = players.getplayer(data[1])
    
    if attacker.name == victim.name:
        attacker.death()
    elif attacker.team == victim.team:
        attacker.teamkill()
        victim.death()
    else:
        attacker.kill()
        victim.death()
    
    players.addkill(attacker, victim, headshot, weapon)

def onPlayerSpawn(players, data):
    console.debug('%s spawned' % data[0])
    player = players.getplayer(data[0])
    if player is None:
        players.connect(data[0])
        player = players.getplayer(data[0])
    player.kit = data[1]
    
def onPlayerChat(players, data):
    console.debug('%s: %s' % (data[0], data[1]))
    who = players.getplayer(data[0])
    chat = data[1]
    target = data[2]
    
    if chat.startswith('/'):
        chat = chat[:1]
        
    for word in kickwords:
        if re.search('\\b' + word + '\\b', chat, re.I):
            if who.warning:
                console.info('kicking %s for bad language' % who.name)
            else:
                console.info('warning %s for bad language' % who.name)
                who.warning = 1
    
    for word in banwords:
        if re.search('\\b' + word + '\\b', chat, re.I):
            console.info('banning %s for really bad language' % who.name)
            
    players.addchat(who, '%s: %s' % (target, chat))
            
def onPlayerSquadchange(players, data):
    console.debug('SquadChange: %s - %s/%s' % (data[0], data[1], data[2]))
    onPlayerTeamchange(players, data)
    
def onPlayerTeamchange(players, data):
    console.debug('TeamChange: %s - %s/%s' % (data[0], data[1]. data[2]))
    
def onPunkbusterMessage(players, data):
    console.debug('%s' % data)   
    for regex, name in PBMessages:
        match = re.match(regex, str(data[0]).strip())
        if match:
            if match and hasattr(punkbuster, name):
                getattr(punkbuster, name)(players, match)
                return
            else:
                console.warning('todo:', data)