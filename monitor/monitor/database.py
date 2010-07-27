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
        self.dbname = config.get('mysql', 'db')
        #self.tempdir = os.path..join('monitor\\')
        os.path.walk(os.path.join('temp/'), self.pickle_to_db, None)

    def open(self):
        if not self.error:
            try:
                self.sql = sqlalchemy.create_engine("mysql://%s:%s@%s/%s" % (self.user, self.passwd, self.host, self.dbname)).connect()
                self.db = sqlalchemy.Table('player_info', sqlalchemy.MetaData(self.sql), autoload=True)
            except Exception, error:
                console.error('Could not connect to DB: %s' % error)
                functions.mail('SQL ERRORS AHEAD', 'You\'ve received this email because\nMonitor failed to \
                               connect to the db.\n The error was:\n %s' % error)
                self.error = True
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
                sql = sqlalchemy.create_engine("mysql://%s:%s@%s/%s" % \
                    (self.user, self.passwd, self.host, self.dbname)).connect()
                db = sqlalchemy.Table('player_info', sqlalchemy.MetaData(sql), autoload=True)
            except:
                console.info('db still not accessible')
                sql = None
                time.sleep(100)
        self.error = False
        console.info('SQL error resolved.. writing files to db...')
        os.path.walk(os.path.join('temp/'), self.pickle_to_db, None)
                           
                
    def write_player(self, player):
        self.open()
        time.sleep(1)
        if self.error:
            #THE RETURN OF THE PICKLE
            console.info('picking player %s' % player.name)
            pickle.dump(player, open(os.path.join('temp/', player.pbid), 'w'))
        else:
            today = time.strftime('%m/%d/%Y', time.localtime())
            current = self.db.select(self.db.c.player_name == player.name).execute().fetchone()
            if current:
                timesSeen = int(current['times_seen']) + 1
                self.db.update(self.db.c.player_name == player.name).execute(clan_tag=player.tag, 
                    ip=player.ip, guid=player.pbid, times_seen=timesSeen, last_seen=today)
            else:
                self.db.insert().execute(player_name=player.name, clan_tag=player.tag, 
                    ip=player.ip, guid=player.pbid, times_seen=1, first_seen=today, last_seen=today)
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
            self.write_player(pickle.load(open(os.path.join('temp/', file), 'r')))
            os.remove(os.path.join('temp/', file))
            print 
            

