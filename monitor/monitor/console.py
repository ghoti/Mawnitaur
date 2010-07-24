'''
Created on Jul 19, 2010

@author: ghoti
'''
import logging

'''
Logging is currently to stdout, and the level is configurable.
This does not configure Tornados output level, only Monitor.
Each module also can get their own logger for easier debugging
'''
class Logger(object):
    def __init__(self, level_name):
        LEVELS = {'debug': logging.DEBUG,
                  'info': logging.INFO,
                  'warning': logging.WARNING,
                  'error': logging.ERROR,
                  'critical': logging.CRITICAL}
        level = LEVELS.get(level_name, logging.NOTSET)
        logging.basicConfig(level=level)
        
        self.console = logging.getLogger('monitor.console')