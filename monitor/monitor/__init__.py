#!/usr/bin/env python

import command
import ConfigParser
import logging
import os
import Queue
import re
import string
import threading
import time

import clients
import console
import events
import functions
import rcon

class Monitor(object):
    def __init__(self):
        self.running = True
        self.rcon = None
        self.eventlisener = None
        self.queue = Queue.Queue()
        
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(os.path.abspath('.') + '/config.cfg'))
        
        #self.console = console.Logger(self.config.get('console', 'level'))
        self.console = console.debuglog(self.config.get('console', 'level'))
        
        self.log = logging.getLogger('monitor')
        
        self.host = self.config.get('server', 'ip')
        self.port = self.config.get('server', 'port')
        self.passw = self.config.get('server', 'pass')
        
        self.players = clients.Clients()
    '''
    go!
    '''
    def start(self):
        threading.Thread(target=self.event_queue).start()
        self.first_run()
        
        while self.running:
            try:
                if not self.rcon:
                    self.log.info('Not connected to server, connecting...')
                    self.rcon = rcon.Rcon(self.host, int(self.port), self.passw)
                    self.rcon.connect()
                    self.rcon.login()
                if not self.eventlisener:
                    self.eventlistener = rcon.Rcon(self.host, int(self.port), self.passw)
                    self.eventlistener.connect()
                    self.eventlistener.login()
                    self.eventlistener.enable_events()
                
                while self.running:
                    event = self.eventlistener.event()
                    try:
                        self.queue.put(event)
                    except SystemExit:
                        self.running = False
                        raise
                    #except Exception, detail:
                    #    self.log.error('%s' % detail)
            except Exception, detail:
                self.log.warning('%s' % detail)
                self.rcon.serverSocket.close()
                self.eventlistener.serverSocket.close()
    '''
    Sending events to a queue lets us continue grabbing events and not be worried
    about bottlenecks, like db access, file IO, etc.  Losing data are bad.
    '''   
    def event_queue(self):
        while self.running:
            if not self.queue.empty():
                event = self.queue.get()
                if not event:
                    self.log.debug('Can not route empty packet?!')
                type = event[0]
                data = event[1:]
                match = re.search(r"^(?P<actor>[^.]+)\.on(?P<event>.+)$", type)
                if match:
                    func = 'on%s%s' % (string.capitalize(match.group('actor')), string.capitalize(match.group('event')))
                    if hasattr(events, func):
                        func = getattr(events, func)
                        event = func(self.players, data, self.rcon)
                        if event:
                            self.queue.put(event)
                    else:
                        self.log.warning('TODO: %s' % func)
            time.sleep(.001)  
    '''
    This is run the first time monitor is ran.  This connects all players, grabs some initial data.
    We also set the map, gametype, and ticket counts here too.
    '''                    
    def first_run(self):
        self.players.addchat('Server', 'There is hope!  Monitor has a pulse!')
        if not self.rcon:
            self.rcon = rcon.Rcon(self.config.get('server', 'ip'), int(self.config.get('server', 'port')), self.config.get('server', 'pass'))
            self.rcon.connect()
            self.rcon.login()
        '''
        OK <serverName: string> <current playercount: integer> <max playercount: integer> 
        <current gamemode: string> <current map: string> 
        <roundsPlayed: integer> <roundsTotal: string> <scores: team scores>
        '''
        initialdata = self.rcon.send('serverInfo')
        self.servername = initialdata[1]
        self.currentplayers = initialdata[2]
        self.maxplayers = initialdata[3]
        self.gametype = initialdata[4]
        self.map = initialdata[5].strip('Levels/')
        self.currentround = initialdata[6]
        self.totalrounds = initialdata[7]
        self.team1score = initialdata[9]
        self.team2score = initialdata[10]
        self.serverrank, self.serverperc = functions.rank_scrape()
        
        initialdata = self.rcon.send('admin.listPlayers', 'all')
        initialdata = initialdata[1:]
        numparms = int(initialdata.pop(0))
        initialdata = initialdata[numparms:]
        for p in xrange(int(initialdata.pop(0))):
            self.players.connect(initialdata[1])
            player = self.players.getplayer(initialdata[1])
            player.tag = initialdata.pop(0)
            initialdata.pop(0)
            player.eaid = initialdata.pop(0)
            player.team = initialdata.pop(0)
            player.squad = initialdata.pop(0)
            player.kills = int(initialdata.pop(0))
            player.deaths = int(initialdata.pop(0))
            initialdata.pop(0)
            initialdata.pop(0)
            threading.Thread(target=functions.player_rank, args=[player]).start()
            #for i in xrange(numparms):
                #print initialdata.pop(0)
        self.rcon.disconnect()
        threading.Thread(target=self.scorewatch).start()
        
    def scorewatch(self):
        while self.running:
            try:
                data = self.rcon.send('serverInfo')
                self.team1score = data[9]
                self.team2score = data[10]
                self.map = data[5].strip('Levels/')
                self.gametype = data[4]
            except Exception, error:
                self.log.error('error in watching scores %s' % error)
            try:
                self.serverrank, self.serverperc = functions.rank_scrape()
            except Exception, error:
                self.log.error('error in scraping rank: %s' % error)
            time.sleep(20)