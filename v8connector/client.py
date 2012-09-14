from twisted.internet import reactor, protocol
from twisted.python import log
import sys
import re
import json
import pprint
import utils

reload(utils)


class V8DebuggerProtocol(protocol.Protocol):
    '''
    Twisted V8 Debugging protocol
    All credit to https://github.com/dannycoates/node-inspector on which much
    of this code is based.
    '''
    def __init__(self):
        self.__buffer = ''
        self.__msg = None
        self.emitter = utils.EventHook()

    def __parse(self):
        if not self.__msg is None and self.__msg["headersDone"]:
            if len(self.__buffer) >= self.__msg["contentLength"]:
                self.__msg["body"] = self.__buffer[0:self.__msg["contentLength"]]
                self.__buffer = self.__buffer[self.__msg["contentLength"]:]
                if len(self.__msg["body"]) > 0:
                    obj = json.loads(self.__msg["body"])
                    pprint.pprint(obj)
                    if obj['type'] == 'response' and obj['request_seq'] > 0:
                        # callback handler
                        pass
                    elif obj['type'] == 'event':
                        #event emitting
                        self.emitter.fire(obj['event'], obj)
                        pass

                self.__msg = None
                self.__parse()
            return

        if not self.__msg:
            self.__msg = {
                'headersDone': False,
                'headers': None,
                'contentLength': 0
            }

        offset = self.__buffer.find('\r\n\r\n')

        if offset > 0:
            self.__msg["headersDone"] = True
            self.__msg["headers"] = self.__buffer[0:offset + 4]
            contentLengthMatch = re.search(r'Content-Length: (\d+)',
                self.__msg["headers"]).groups()
            if contentLengthMatch[0]:
                self.__msg["contentLength"] = int(contentLengthMatch[0])
            else:
                print "No content length"
            self.__buffer = self.__buffer[offset + 4:]
            self.__parse()

    def dataReceived(self, data):
        # print data
        self.__buffer += data
        self.__parse()

    def connectionMade(self):
        s = json.dumps({
           'seq': 101,
           'type': 'request',
           'command': 'continue'
        })
        msg = 'Content-Length: {0}\r\n\r\n{1}'.format(len(s), s)
        self.transport.write(msg)


class V8DebuggerClientFactory(protocol.ClientFactory):

    def startedConnecting(self, connector):
        print 'Started to connect.'

    def buildProtocol(self, addr):
        print 'Connected.'
        protocol = V8DebuggerProtocol()
        self.vent = protocol.emitter
        return protocol

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason
