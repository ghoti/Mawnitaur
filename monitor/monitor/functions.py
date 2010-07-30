'''
Created on Jul 25, 2010

@author: ghoti
'''
import ConfigParser
import logging
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from os import path
import smtplib
import urllib
import simplejson as json
import time
import re

console = logging.getLogger('monitor.func')

matchrank = re.compile('(?P<rank>\d+)(?P<ranksuf>\D{2})\s\(<span>(?P<percentile>\d+)(?P<percentsuf>\D{2})')

def mail(subject, text):
    try:
        config = ConfigParser.ConfigParser()
        config.readfp(open(path.abspath('.') + '\\config.cfg'))
        msg = MIMEMultipart()
        
        msg['From'] = config.get('email', 'user')
        msg['To'] = config.get('email', 'send_to')
        msg['Subject'] = subject
        emailpass = config.get('email', 'pass')
        
        msg.attach(MIMEText(text))
        
        #part = MIMEBase('application', 'octet-stream')
        
        mailServer = smtplib.SMTP("smtp.gmail.com", 587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(msg['From'], emailpass)
        mailServer.sendmail(msg['From'], msg['To'], msg.as_string())
        # Should be mailServer.quit(), but that crashes...
        mailServer.close()
    except Exception, error:
        console.error('Email could not be sent! %s' % error)
        
def player_rank(player):
    while True:
        try:
            url = 'http://api.bfbcs.com/api/pc?players=%s&fields=general' % player.name
            webFile = urllib.urlopen(url)
            rank = webFile.read()
            data = json.loads(rank)
            player.rank = str(data['players'][0]['rank'])
            return
        except Exception, detail:
            console.error('error fetching rank: %s' % detail)
            #got to sleep, sometimes the player doesn't exist with this api yet, and we need time to let it update
            time.sleep(60)
            
def rank_scrape():
    try:
        content = urllib.urlopen("http://www.gametracker.com/server_info/68.232.162.167:19567/").read()
        m = re.search(matchrank, content)
        if m:
            rank = m.group('rank') + m.group('ranksuf')
            percent = m.group('percentile') + m.group('percentsuf')
        else:
            rank = 'Unkmown'
            percent = 'Unknown'
        return [rank, percent]
    except Exception, error:
        console.error('Error scraping gt rank: %s' % error)