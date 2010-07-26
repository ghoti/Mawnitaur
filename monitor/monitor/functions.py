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