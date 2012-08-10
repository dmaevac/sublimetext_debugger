
        # s = json.dumps({
        #    'seq': 101,
        #    'type': 'request',
        #    'command': 'continue'
        # })
        # msg = 'Content-Length: {0}\r\n\r\n{1}'.format(len(s), s)
        # self.buffer = msg

        # s = json.dumps({
        #    'seq': 102,
        #    'type': 'request',
        #    'command': 'listbreakpoints',
        #    'arguments': {
        #         'types': 4,
        #         'includeSource': True
        #    }
        # })
        # msg = 'Content-Length: {0}\r\n\r\n{1}'.format(len(s), s)
        # self.buffer = msg
# twisted imports
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import sys
import re
import json
import pprint


class V8DebuggerProtocol(protocol.Protocol):
    def __init__(self):
        self.__buffer = ''
        self.__msg = None

    def __parse(self):
        if not self.__msg is None and self.__msg["headersDone"]:
            if len(self.__buffer) >= self.__msg["contentLength"]:
                self.__msg["body"] = self.__buffer[0:self.__msg["contentLength"]]
                self.__buffer = self.__buffer[self.__msg["contentLength"]:]
                if len(self.__msg["body"]) > 0:
                    obj = json.loads(self.__msg["body"])
                    pprint.pprint(obj)
        #   if (obj.type === 'response' && obj.request_seq > 0) {
        #     callbackHandler.processResponse(obj.request_seq, [obj]);
        #   }
        #   else if (obj.type === 'event') {
        #     debugr.emit(obj.event, obj);
        #   }
        # }

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
        return V8DebuggerProtocol()

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason

if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)

    # create factory protocol and application
    f = V8DebuggerClientFactory()

    # connect factory to this host and port
    reactor.connectTCP("localhost", 9222, f)

    # run bot
    reactor.run()
