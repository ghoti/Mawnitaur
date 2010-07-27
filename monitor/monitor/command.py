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
                 '!chuck':'Public', '!stats':'Public', '!rules':'Public', '!punish':'Recruit'
                }

genericcommand = re.compile(r'^(?P<cid>\'[^\']{2,}\'|[0-9]+|[^\s]{2,}|@[0-9]+)\s?(?P<parms>.*)$', re.I)

'''
Nothing to see here yet, move along.

Will eventually contain all in-game commands used by admins to police server
'''
def command(player, chat, rcon, players):
    if re.search('!rules', chat, re.I):
        rules(player, rcon)
    elif re.search('!chuck', chat, re.I):
        chuck(rcon)
    elif re.search('!help', chat, re.I):
        help(player, rcon)
    elif chat.lower().startswith('!punish') and player.power == 'Recruit':
        punish(player, chat, rcon, players)
        
def rules(player, rcon):
    console.debug('%s has called !rules' % player.name)
    with open('rules.txt', 'r') as f:
        for line in f:
            rcon.send('admin.say', line.strip('\n'), 'player', player.name)
            time.sleep(2)
            
def chuck(rcon):
    fact = getline('chuck.txt', randint(1, 66)).replace('\"', '').replace("\'", '')
    rcon.send('admin.say', fact, 'all')
    
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
            