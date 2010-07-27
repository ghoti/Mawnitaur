'''
Created on Jul 19, 2010

@author: ghoti
'''
from __future__ import with_statement
import logging
import re

import command
import database
import punkbuster

#Set the logger
console = logging.getLogger('monitor.events')

#Fill the auto-kick words
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

db = database.Database()

#player.onJoin <soldier name: string>
def onPlayerJoin(players, data, rcon):
    console.debug('%s connected' % data[0])
    players.connect(data[0])
    p = players.getplayer(data[0])
    

#player.onAuthenticated <soldier name: string> <player GUID: guid>
def onPlayerAuthenticated(players, data, rcon):
    console.debug('%s received ea_guid' % data[0])
    p = players.getplayer(data[0])
    if p is None:
        players.connect(data[0])
    p.eaid = data[1]
        
#player.onLeave <soldier name: string> <soldier info: player info block> 
def onPlayerLeave(players, data, rcon):
    console.debug('%s left' % data[0])
    p = players.getplayer(data[0])
    if p is not None:
        players.disconnect(data[0])

#player.onKill <killing soldier name: string> <killed soldier name: string> <weapon: string> 
#<headshot: boolean> <killer location: 3 x integer> <killed location: 3 x integes>        
def onPlayerKill(players, data, rcon):
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

#player.onSpawn <soldier name: string> <kit: string> <weapons: 3 x string> <gadgets: 3 x string>
def onPlayerSpawn(players, data, rcon):
    console.debug('%s spawned' % data[0])
    player = players.getplayer(data[0])
    if player is None:
        players.connect(data[0])
        player = players.getplayer(data[0])
    player.kit = data[1]

#player.onChat <source soldier name: string> <text: string> <target group: player subset>    
def onPlayerChat(players, data, rcon):
    console.debug('%s: %s: %s' % (data[0], data[1], data[2]))
    if data[0] == 'Server':
        return
    who = players.getplayer(data[0])
    if not who:
        players.connect(data[0])
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
            
    players.addchat(who.name, '%s: %s' % (target, chat))
    command.command(who, chat, rcon, players)

#player.onSquadChange <soldier name: player name> <team: Team ID> <squad: Squad ID>
#NOTE:  We send this info to the teamChange event.  No need to be redundant.. :-p
def onPlayerSquadchange(players, data, rcon):
    console.debug('SquadChange: %s - %s/%s' % (data[0], data[1], data[2]))
    onPlayerTeamchange(players, data, rcon)
    
#player.onTeamChange <soldier name: player name> <team: Team ID> <squad: Squad ID>
def onPlayerTeamchange(players, data, rcon):
    console.debug('TeamChange: %s - %s/%s' % (data[0], data[1], data[2]))
    p = players.getplayer(data[0])
    if not p:
        players.connect(data[0])
        p = players.getplayer(data[0])
    p.team = data[1]

#player.onKicked <soldier name: string> <reason: string> 
def onPlayerKicked(players, data, rcon):
    console.debug('Kicked: %s - %s' % (data[0], data[1]))
    
#server.onRoundOver <winning team: Team ID>
def onServerRoundover(players, data, rcon):
    console.debug('Round Over: Winners - Team %s' % data[0])
    players.addchat('Server', 'Round Over.  Winners: Team %s' % data[0])
    
#server.onRoundOverPlayers <end-of-round soldier info : player info block>
def onServerRoundoverplayers(players, data, rcon):
    console.debug('Round Over Scores')

#server.onRoundOverTeamScores <end-of-round scores: team scores> 
def onServerRoundOverTeamscores(players, data, rcon):
    console.debug('Round Over Team Scores: Team 1: %s - Team 2: %s' % (data[0], data[1]))
    players.addchat('Server', 'Round scores - Team 1: %s - Team 2: %s' % (data[0], data[1]))
        
#punkBuster.onMessage <message: string>
#Match a punkbuster message to a set of known/used messages and handle that data elsewhere.
def onPunkbusterMessage(players, data, rcon):
    for regex, name in PBMessages:
        match = re.match(regex, str(data[0]).strip())
        if match:
            if match and hasattr(punkbuster, name):
                getattr(punkbuster, name)(players, match)
                return
            else:
                console.warning('todo:', data)