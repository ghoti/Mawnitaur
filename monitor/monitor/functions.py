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
import urllib2 as urllib
import simplejson as json
import time

console = logging.getLogger('monitor.func')

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