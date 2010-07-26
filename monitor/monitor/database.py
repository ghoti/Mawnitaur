'''
Created on Jul 25, 2010

@author: ghoti
'''
import ConfigParser
import cPickle as pickle
import logging
import functions
import sqlalchemy
import threading
import time
import os

from os import path

console = logging.getLogger('monitor.database')

class Database(object):
    def __init__(self):
        self.sql = None
        self.error = False
        config = ConfigParser.ConfigParser()
        config.readfp(open(path.abspath('.') + '\\config.cfg'))
        self.host = config.get('mysql', 'host')
        self.user = config.get('mysql', 'user')
        self.passwd = config.get('mysql', 'passwd')
        self.db = config.get('mysql', 'db')
        self.tempdir = config.get('temp', 'dir')

    def open(self):
        if not self.error:
            try:
                self.sql = sqlalchemy.create_engine("mysql://%s:%s@%s/%s" % (self.user, self.passwd, self.host, self.db)).connect()
                self.db = sqlalchemy.Table('player_info', sqlalchemy.MetaData(self.sql), autoload=True)
            except Exception, error:
                console.error('Could not connect to DB: %s' % error)
                functions.mail('SQL ERRORS AHEAD', 'You\'ve received this email because\nMonitor failed to \
                               connect to the db.\n The error was:\n %s' % error)
                error = True
                threading.Thread(target=self.sql_watch).start()
                
    def close(self):
        if self.sql:
            try:
                self.sql.close()
            except:
                pass
            self.sql = None
            
    def sql_watch(self):
        while self.error:
            try:
                self.sql = sqlalchemy.create_engine("mysql://%s:%s@%s/%s" % \
                    (self.user, self.passwd, self.host, self.db)).connect()
            except:
                self.sql = None
                time.sleep(600)
        console.info('SQL error resolved.. writing files to db...')
        os.path.walk(self.tempdir, self.pickle_to_db, None)
                
    def write_player(self, player):
        self.open()
        if not self.error:
            today = time.strftime('%m/%d/%Y', time.localtime())
            current = self.db.select(self.db.c.player_name == player.name).execute().fetchone()
            if current:
                timesSeen = int(current['times_seen']) + 1
                self.db.update(self.db.c.player_name == player.name).execute(clan_tag=player.tag, 
                    ip=player.ip, guid=player.pbid, times_seen=timesSeen, last_seen=today)
            else:
                self.db.insert().execute(player_name=player.name, clan_tag=player.tag, 
                    ip=player.ip, guid=player.pbid, times_seen=1, first_seen=today, last_seen=today)
        else:
            #THE RETURN OF THE PICKLE
            pickle.dump(player, open(self.tempdir + player.name, 'ab'))
        self.close()

    def has_been_seen(self, player):
        self.open()
        if not self.error:
            p = self.db.select(self.db.c.player_name == player.name).execute()
            if p.fetchone():
                return True
            else:
                return False
        self.close()
    
    def pickle_to_db(self, arg, dir, files):
        for file in files:
            self.write_player(pickle.load(self.tempdir + file), 'r')
            os.remove(self.tempdir + file)
            

