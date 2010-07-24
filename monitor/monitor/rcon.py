import logging
import socket

import bc2connection as protocol
from pickle import PROTO

class Rcon(object):
    def __init__(self, host, port, pw):
        self.host = host
        self.port = port
        self.pw = pw
        self.serverSocket = None
        
        self.console = logging.getLogger('monitor.rcon')
        
    
    def connect(self):
        try:
            self.console.debug('connecting to %s:%i - %s' % (self.host, self.port, self.pw))
            self.clientSequenceNr = 0
            self.receiveBuffer = ''
            self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serverSocket.connect( ( self.host, self.port ) )
            self.serverSocket.setblocking(1)
        except socket.error, detail:
            self.console.critical('Could not connect to server: %s' % detail)
            
    def disconnect(self):
        if self.serverSocket is not None:
            pass
        
    def login(self):
        if self.serverSocket is None:
            raise Exception('Not connected to server')
        
        words = self.send('login.hashed')
        if words[0] != 'OK':
            raise Exception('Failed to retrieve login info')
        
        salt = words[1].decode('hex')
        passHash = protocol.generatePasswordHash(salt, self.pw)
        passHashHex = protocol.string.upper(passHash.encode('hex'))
        
        response = self.send('login.hashed', passHashHex)
        
        if response[0] != 'OK':
            raise Exception('Incorrect Password!')
        
        
    def send(self, *command):
        if not command:
            pass
        if self.serverSocket is None:
            self.console.debug('not connected, reconnecting...')
            self.connect()
            self.login()
        if len(command) == 1 and type(command[0]) == tuple:
            words = command[0]
        else:
            words = command
        request = protocol.EncodeClientRequest(words)
        self.console.debug(words)
        try:
            self.serverSocket.sendall(request)
            response, self.receiveBuffer = protocol.receivePacket(self.serverSocket, self.receiveBuffer)
        except socket.error, detail:
            raise Exception('error sending: %s', detail)
        if not response:
            return None
        response = protocol.DecodePacket(response)
        return response[3]
        
    def enable_events(self):
        self.console.debug('enabling events')
        response = self.send('eventsEnabled', 'true')
        
        if response[0] != 'OK':
            raise Exception(response)
        
    def event(self):
        packet = None
        timeout = 0
        error = 0
        
        while packet is None:
            try:
                if self.serverSocket is None:
                    self.console.info('event: reconnecting...')
                    self.connect()
                    self.login()
                    self.enable_events()
                temp, self.receiveBuffer = protocol.receivePacket(self.serverSocket, self.receiveBuffer)
                isFromServer, isResponse, sequence, words = protocol.DecodePacket(temp)
                if isFromServer and not isResponse:
                    packet = temp
                else:
                    self.console.info('received non-event packet: %s' % words)
                
            except socket.timeout:
                timeout += 1
                self.console.debug('timeout! %s' % timeout)
                if timeout >= 5:
                    request = protocol.EncodeClientRequest(['eventsEnabled', 'true'])
                    self.serverSocket.sendall(request)
                    timeout = 0
            except socket.error, detail:
                raise Exception('error in server connection?!')
        
        try:
            isFromServer, isResponse, sequence, words = protocol.DecodePacket(packet)
        except:
            self.console.warning('failed to decode packet: %r' % packet)
        
        if isResponse:
            self.console.info('got unexpected packet, ignoring %r' % packet)
            return self.event()
        else:
            response = protocol.EncodePacket(True, True, sequence, ['OK'])
            try:
                self.serverSocket.sendall(response)
            except socket.error, detail:
                self.console.warning('error in sending OK response: %s' % detail)
            return words