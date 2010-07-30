'''
Created on Jul 20, 2010

@author: ghoti
'''
import monitor
import flask
import threading
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

'''
Start Monitor
'''
m = monitor.Monitor()
threading.Thread(target=m.start).start()

'''
Create our wsgi object (a fancy name for the status page, heh
'''
mon = flask.Flask(__name__)
#mon.debug = True


'''
return flask.render_template('status.html', host=self.host, map=self.map_name(self.map) + ' ' + self.round[0] + '/' + self.round[1], gametype=(self.gametype[0].upper() + self.gametype[1:]),\
pcount=self.pcount, mapfile=self.map, kills=reversed(self.kills), chat=reversed(self.chat), team1=self.players.getTeam('1'), team2=self.players.getTeam('2'), rank=self.serverrank, percent=self.serverperc, \
scores=self.scores)
'''
@mon.route('/')
def index():
    return flask.render_template('status.html', host=m.host, map=m.map, \
        gametype=m.gametype, scores=[m.team1score, m.team2score], pcount=len(m.players), \
        kills=reversed(m.players.kills), chat=reversed(m.players.lastchat), \
        team1=m.players.getteam('1'), team2=m.players.getteam('2'), rank=m.serverrank, \
        percent=m.serverperc)
    
@mon.route('/pcount.html')
def count():
    return '<html>\n<head>\n<title></title>\n</head>\n<body style="color: #ffffff; background-color: #000000;  font-size: 12px; font-family: Verdana, Arial, Helvetica, sans-serif;">\n \
                %s / 32\n</body>\n</html>' % len(m.players)

'''
Start the status page.  It would seem that _now_ ctrl-c is sufficient to kill everything
'''
http_server = HTTPServer(WSGIContainer(mon))
http_server.listen(8088)
IOLoop.instance().start()
#mon.run()

