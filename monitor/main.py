'''
Created on Jul 20, 2010

@author: ghoti
'''
import monitor
import flask
import threading
import time
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
m = monitor.Monitor()
threading.Thread(target=m.start).start()

mon = flask.Flask(__name__)
mon.debug = True

'''
return flask.render_template('status.html', host=self.host, map=self.map_name(self.map) + ' ' + self.round[0] + '/' + self.round[1], gametype=(self.gametype[0].upper() + self.gametype[1:]),\
pcount=self.pcount, mapfile=self.map, kills=reversed(self.kills), chat=reversed(self.chat), team1=self.players.getTeam('1'), team2=self.players.getTeam('2'), rank=self.serverrank, percent=self.serverperc, \
scores=self.scores)
'''
@mon.route('/')
def index():
    return flask.render_template('status.html', host=m.host, map=m.map, \
        gametype=m.gametype, scores=[0,0], pcount=len(m.players), \
        kills=reversed(m.players.kills), chat=reversed(m.players.lastchat), \
        team1=m.players.getteam('1'), team2=m.players.getteam('2'))


http_server = HTTPServer(WSGIContainer(mon))
http_server.listen(8088)
IOLoop.instance().start()
#mon.run()

