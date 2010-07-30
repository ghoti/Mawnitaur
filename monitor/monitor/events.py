'''
Created on Jul 19, 2010

@author: ghoti
'''
from __future__ import with_statement
import linecache
import ConfigParser
import logging
import logging.handlers
import glob
import random
import re
import string
import threading

import command
import console
import database
import punkbuster
from functions import player_rank

#Set the logger
config = ConfigParser.ConfigParser()
config.readfp(open(os.path.abspath('.') + '/config.cfg'))
output = logging.getLogger('monitor.events')
output.setLevel(int(config.get('console', 'level')))

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

gamelog = logging.getLogger('eventlog')
gamelog.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler('../logs/gamelog.txt', maxBytes=1048576, backupCount=100)
handler.setFormatter(logging.Formatter("%(created)f;%(message)s"))
gamelog.addHandler(handler)
chatlog = logging.getLogger('chatlog')
chatlog.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler('../logs/chatlog.txt', maxBytes=1048576, backupCount=100)
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%m-%d-%Y %H;%M;%S'))
chatlog.addHandler(handler)


#player.onJoin <soldier name: string>
def onPlayerJoin(players, data, rcon):
    output.debug('%s connected' % data[0])
    gamelog.info('onJoin;' + ';'.join(data))
    players.connect(data[0])
    p = players.getplayer(data[0])
    seen = db.has_been_seen(p)
    threading.Timer(60, welcome_messager, args=[p, rcon, seen]).start()
    

#player.onAuthenticated <soldier name: string> <player GUID: guid>
def onPlayerAuthenticated(players, data, rcon):
    output.debug('%s received ea_guid' % data[0])
    p = players.getplayer(data[0])
    if p is None:
        players.connect(data[0])
    p.eaid = data[1]
        
#player.onLeave <soldier name: string> <soldier info: player info block> 
def onPlayerLeave(players, data, rcon):
    output.debug('%s left' % data[0])
    gamelog.info('onLeave;' + data[0])
    p = players.getplayer(data[0])
    if p is not None:
        players.disconnect(data[0])

#player.onKill <killing soldier name: string> <killed soldier name: string> <weapon: string> 
#<headshot: boolean> <killer location: 3 x integer> <killed location: 3 x integes>        
def onPlayerKill(players, data, rcon):
    output.debug('%s killed %s' % (data[0], data[1]))
    gamelog.info('onKill;' + ';'.join(data))
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
        if attacker.streak >= 10:
            streak = string.Template(linecache.getline('streakend.txt', random.randint(1,4)))
            streak = streak.substitute(victag=victim.tag, vicname=victim.name, streak=str(victim.streak), killertag=attacker.tag, killername=attacker.name).strip('\n')
            rcon.send('admin.say', streak, 'all')
        attacker.death()
    elif attacker.team == victim.team:
        rcon.send('admin.say', '%s just TEAMKILLED %s!!!', 'all')
        attacker.teamkill()
        victim.death()
    else:
        attacker.kill()
        if not attacker.streak % 10:
            streak = string.Template(linecache.getline('streak.txt', random.randint(1,5)))
            streak = streak.substitute(tag=attacker.tag, name=attacker.name, streak=str(attacker.streak)).strip('\n')
            rcon.send('admin.say', streak, 'all')
        if victim.streak >= 10:
            streak = string.Template(linecache.getline('streakend.txt', random.randint(1,4)))
            streak = streak.substitute(victag=victim.tag, vicname=victim.name, streak=str(victim.streak), killertag=attacker.tag, killername=attacker.name).strip('\n')
            rcon.send('admin.say', streak, 'all')
        victim.death()
    
    players.addkill(attacker, victim, headshot, weapon)

#player.onSpawn <soldier name: string> <kit: string> <weapons: 3 x string> <gadgets: 3 x string>
def onPlayerSpawn(players, data, rcon):
    output.debug('%s spawned' % data[0])
    player = players.getplayer(data[0])
    if player is None:
        players.connect(data[0])
        player = players.getplayer(data[0])
    player.kit = data[1]

#player.onChat <source soldier name: string> <text: string> <target group: player subset>    
def onPlayerChat(players, data, rcon):
    output.debug('%s: %s: %s' % (data[0], data[1], data[2]))
    if data[0] == 'Server':
        return
    chatlog.info(' - '.join(data))
    gamelog.info('onChat;' + ';'.join(data))
    who = players.getplayer(data[0])
    if not who:
        players.connect(data[0])
        who = players.getplayer(data[0])
    chat = data[1]
    target = data[2]
    
    if chat.startswith('/'):
        chat = chat[:1]
        target = 'Private'
        
    for word in kickwords:
        if re.search('\\b' + word + '\\b', chat, re.I):
            if who.warning:
                output.info('kicking %s for bad language' % who.name)
                rcon.send('punkBuster.pb_sv_command', 'PB_SV_Kick %s 10 That Language is not Tolerated here.' % (who.name))
            else:
                output.info('warning %s for bad language' % who.name)
                who.warning = 1
                rcon.send('admin.say', 'That language is NOT tolerated here!  This is your only warning!',
                          'player', who.name)
    
    for word in banwords:
        if re.search('\\b' + word + '\\b', chat, re.I):
            output.info('banning %s for really bad language' % who.name)
            rcon.send('punkBuster.pb_sv_command', 'pb_sv_banGUID %s %s %s %s' % (who.pbid, 
                      who.name, who.ip, 'Monitor Language Ban'))
            
    players.addchat(who.name, '%s: %s' % (target, chat))
    command.command(who, chat, rcon, players)

#player.onSquadChange <soldier name: player name> <team: Team ID> <squad: Squad ID>
#NOTE:  We send this info to the teamChange event.  No need to be redundant.. :-p
def onPlayerSquadchange(players, data, rcon):
    output.debug('SquadChange: %s - %s/%s' % (data[0], data[1], data[2]))
    onPlayerTeamchange(players, data, rcon)
    
#player.onTeamChange <soldier name: player name> <team: Team ID> <squad: Squad ID>
def onPlayerTeamchange(players, data, rcon):
    output.debug('TeamChange: %s - %s/%s' % (data[0], data[1], data[2]))
    p = players.getplayer(data[0])
    if not p:
        players.connect(data[0])
        p = players.getplayer(data[0])
    p.team = data[1]

#player.onKicked <soldier name: string> <reason: string> 
def onPlayerKicked(players, data, rcon):
    output.debug('Kicked: %s - %s' % (data[0], data[1]))
    chatlog.info(' - '.join(data))
    players.addchat(data[0], data[1])
    rcon.send('admin.say', 'Kicked %s for %s' % (data[0], data[1][:99]), 'all')
    
#server.onRoundOver <winning team: Team ID>
def onServerRoundover(players, data, rcon):
    output.debug('Round Over: Winners - Team %s' % data[0])
    players.addchat('Server', 'Round Over.  Winners: Team %s' % data[0])
    rcon.send('admin.say', 'Congratulations to Team %s' % data[0], 'all')
    
#server.onRoundOverPlayers <end-of-round soldier info : player info block>
def onServerRoundoverplayers(players, data, rcon):
    output.debug('Round Over Scores')

#server.onRoundOverTeamScores <end-of-round scores: team scores> 
def onServerRoundoverTeamscores(players, data, rcon):
    output.debug('Round Over Team Scores: Team 1: %s - Team 2: %s' % (data[0], data[1]))
    players.addchat('Server', 'Round scores - Team 1: %s - Team 2: %s' % (data[0], data[1]))

#server.onLoadingLevel  <level name: string> <roundsPlayed: int> <roundsTotal: int>
def onServerLoadinglevel(players, data, rcon):
    output.debug('Loading Level...' + ','.join(data))
    players.addchat('Server', 'Map Changed to %s - Round %s of %s' % (data[0], data[1], data[2]))
    
def onServerLevelstarted(players, data, rcon):
    output.debug('LevelStarted...' + ','.join(data))
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
                output.warning('todo:', data)
                
def welcome_messager(player, rcon, seen):
    data = rcon.send('admin.listPlayers', 'player', player.name)
    if data:
        player.tag = data[12]
        player.eaguid = data[14]
        player.team = data[15]
        player.squad = data[16]
        player.kills += int(data[17])
        player.deaths += int(data[18])
    if player.message == '\n':
        rcon.send('admin.yell', player.message.strip('\n'), '3000', 'player', player.name)
    else:
        if seen:
            rcon.send('admin.yell', 'Welcome back to JHF, %s %s! Be sure to visit jhfgames.com and get to know us!' %
                      (player.tag, player.name), '3000', 'player', player.name)
        else:
            rcon.send('admin.yell', 'Welcome to JHF, %s %s! Play fair, Have fun and visit us at jhfgames.com sometime!' %
                      (player.tag, player.name),'3000', 'player', player.name)
    player_rank(player)
        