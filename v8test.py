from v8connector import client
from twisted.internet import reactor


def on_vent(self, name, data):
    print 'vented'

if __name__ == '__main__':
    # create factory protocol and application
    f = client.V8DebuggerClientFactory()

    # connect factory to this host and port
    reactor.connectTCP("localhost", 9222, f)

    # run bot
    reactor.run()

    f.vent += on_vent
