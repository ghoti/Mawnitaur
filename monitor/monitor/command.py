'''
Created on Jul 19, 2010

@author: ghoti
'''
import logging

'''
Nothing to see here yet, move along.

Will eventually contain all in-game commands used by admins to police server
'''
class Command(object):
    def __init__(self):
        self.console = logging.getLogger('monitor.command')
    def kick(self):
        self.console.debug('kick!')
    def Chat(self):
        self.console.debug('chat!')
    def PunkBuster(self):
        self.console.debug('Punkbuster!')