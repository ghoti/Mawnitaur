'''
Created on Jul 19, 2010

@author: ghoti
'''
from __future__ import with_statement
import logging
import re
import time
from random import randint
from linecache import getline

console = logging.getLogger('monitor.func')

commandlevels = {
                 '!chuck':'Public', '!stats':'Public', '!rules':'Public', '!punish':'Recruit',
                 '!map':'Recruit',
                }

adminlevels = {'Public':0, 'Recruit':1, 'Admin':2, 'Super':3}

genericcommand = re.compile(r'^(?P<cid>\'[^\']{2,}\'|[0-9]+|[^\s]{2,}|@[0-9]+)\s?(?P<parms>.*)$', re.I)

'''
Nothing to see here yet, move along.

Will eventually contain all in-game commands used by admins to police server
'''
def command(player, chat, rcon, players):
    if re.search('!rules', chat, re.I):
        rules(player, rcon)
        return
    elif re.search('!chuck', chat, re.I):
        chuck(rcon)
        return
    elif re.search('!help', chat, re.I):
        help(player, rcon)
        return
    elif re.search('!stats', chat, re.I):
        stats(player, rcon)
        return
    elif chat.lower().startswith('!punish') and adminlevels[player.power] >= adminlevels['Recruit']:
        punish(player, chat, rcon, players)
        return
    elif chat.lower().startswith('!map') and adminlevels[player.power] >= adminlevels['Recruit']:
        map(player, rcon)
        return
    elif chat.lower().startswith('!restart') and adminlevels[player.power] >= adminlevels['Recruit']:
        restart(rcon)
        return
    elif chat.lower().startswith('!rotate') and adminlevels[player.power] >= adminlevels['Recruit']:
        rotate(rcon)
        return
    elif chat.lower().startswith('gametype') and adminlevels[player.power] >= adminlevels['Admin']:
        gametype(player, rcon)
        return
        
def rules(player, rcon):
    console.debug('%s has called !rules' % player.name)
    with open('rules.txt', 'r') as f:
        for line in f:
            rcon.send('admin.say', line.strip('\n'), 'player', player.name)
            time.sleep(2)
            
def chuck(rcon):
    fact = getline('chuck.txt', randint(1, 66)).replace('\"', '').replace("\'", '')
    rcon.send('admin.say', fact, 'all')
    
def stats(player, rcon):
    rcon.send('admin.say', '%s: %i kills and %i deaths for a ratio of %.2f' % \
              (player.kills, player.deaths, player.ratio), 'all')
    
def help(player, rcon):
    console.debug('%s called !help' % player.name)
    available = []
    for c, l in commandlevels.items():
        if player.power == l:
            available.append(c)
    rcon.send('Available commands for player %s:' % player.name, 'player', player.name)
    rcon.send(''.join(available), 'player', player.name)
    
def punish(player, chat, rcon, players):
    console.debug('%s called !punish' % player.name)
    m = re.match(genericcommand, chat)
    if m:
        miscreant = players.simple_search(m.group('parms'))
        if miscreant:
            rcon.send('admin.yell', 'You are being punished by a JHF admin for misbehaving.There will be no more warnings!!!',
                      '6000', 'player', miscreant.name)
            time.sleep(2)
            rcon.send('admin.killPlayer', miscreant.name)
        else:
            rcon.send('admin.say', 'Ambiguous player or player not found', 'player', player.name)
            
def map(player, rcon):
    rcon.send('admin.say', '!map is not functional just yet... sorry', 'player', player.name)
    
def restart(rcon):
    rcon.send('admin.restartMap')
    
def rotate(rcon):
    rcon.send('admin.runNextLevel')
    
def gametype(player, rcon):
    rcon.send('admin.say', 'Sorry, !gametype has been disabled temporarily', 'player', 'player.name')
            