'''
Created on Jul 19, 2010

@author: ghoti
'''
from __future__ import with_statement
from time import strftime, localtime
import ConfigParser
import os
import re
import logging

config = ConfigParser.ConfigParser()
config.readfp(open(os.path.abspath('.') + '/config.cfg'))
console = logging.getLogger('monitor.clients')
console.setLevel(int(config.get('console', 'level')))
'''
Player objects hold all our individual player data.
'''
class Player(object):
    def __init__(self, name):
        self.name = name
        self.tag = ''
        self.kills = 0
        self.deaths = 0
        self.ratio = 0.00
        self.streak = 0
        self.suicides = 0
        self.teamkills = 0
        self.ip = '0.0.0.0'
        self.pbid = ''
        self.eaid = ''
        self.team = 0
        self.squad = 0
        self.kit = ''
        self.rank = '#'
        self.warning = 0
        self.power = 'Public'
        self.message = ''
        
    def setteam(self, team):
        self.team = team
    
    def settag(self, tag):
        self.tag = tag
        
    def kill(self):
        self.kills += 1
        self.streak += 1
        if self.deaths == 0:
            self.ratio = self.kills
        else:
            self.ratio = round(float(self.kills)/float(self.deaths), 2)
        
    def death(self):
        self.deaths += 1
        self.streak = 0
        if self.kills == 0:
            self.ratio = 0.00
        else:
            self.ratio = round(float(self.kills)/float(self.deaths),2)
        
    def teamkill(self):
        self.teamkills += 1
        
    def suicide(self):
        self.death()
        self.suicides += 1 
        
'''
Clients is a dict based object that holds all the players, referenced by
player name since BC2 does not dish out slot numbers or any other handy
id method.  All names are unique via EA, so using names _should_ be ok...
Clients also holds the chat log and kill log for the status page
'''
class Clients(dict):
    def __init__(self):
        self.lastchat = []
        self.kills = []
        
    def connect(self, name):
        if not self.has_key(name):
            self[name] = Player(name)
            with open('admins.txt', 'r') as f:
                for line in f:
                    line = line.split(';')
                    if self[name].name == line[0]:
                        self[name].power = line[1]
                        self[name].message = line[2]
                        console.info('%s was given %s power level' % (self[name].name, line[1]))
    
    def disconnect(self, name):
        if self.has_key(name):
            del self[name]
            
    def getplayer(self, name):
        if self.has_key(name):
            return self[name]
        else:
            return None
        
    def getteam(self, team):
        list = []
        for i in self.values():
            if i.team == team:
                list.append(i)
        return list
    
    def simple_search(self, player):
        plist = []
        for p in self.values():
            if re.search(player, p.name, re.I):
                plist.append(p)
        if len(plist) != 1:
            #self.rc.sndcmd(self.rc.SAY, '\'Ambiguous player defined or player not found, try being more specific...\' player \'%s\'' %
            #    player.name)
            
            return None
        else:
            return plist[0]
    
    def addchat(self, player, chat):
        if player:
            if len(self.lastchat) >= 20:
                self.lastchat.pop(0)
            self.lastchat.append('%s - %s: %s' % (strftime("%m/%d %H:%M:%S", localtime()), player, chat))
        
    def addkill(self, attacker, victim, headshot, weapon):
        if len(self.kills) >= 10:
            self.kills.pop(0)
        if attacker.name == victim.name:
            self.kills.append('%s commited suicide with a %s' % (attacker.name, weapon))
        elif attacker.team == victim.team:
            self.kills.append('%s teamkilled %s with a %s' % (attacker.name, victim.name, weapon))
        else:
            if headshot == 'false':
                self.kills.append('%s killed %s with a %s' % (attacker.name, victim.name, weapon))
            else:
                self.kills.append('%s blew %s\'s head off with a %s' % (attacker.name, victim.name, weapon))
            
    