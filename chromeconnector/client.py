import json
from ws4py.client.threadedclient import WebSocketClient
import chromeconnector.debugger
import chromeconnector.runtime
import utils

reload(chromeconnector.debugger)
reload(chromeconnector.runtime)
reload(utils)


class ChromeClient(WebSocketClient):
    def initialize(self, host, vent):
        self._on_notification = utils.EventHook()
        self.debugger = chromeconnector.debugger.Debugger(host, self.send_message, self._on_notification, vent)
        self.runtime = chromeconnector.runtime.Runtime(host, self.send_message, self._on_notification, vent)
        self._idcounter = 1
        self._callbacks = dict()

    def opened(self):
        print "Connection opened..."
        self.debugger.enable()
        self.debugger.can_set_source()

    def closed(self, code, reason=None):
        self.debugger.disable()
        print "Closed down", code, reason

    def send_message(self, method, params=None, callback=None):
        self.send(json.dumps({
            'id': self._idcounter,
            'method': method,
            'params': params
        }))
        if callback:
            self._callbacks[self._idcounter] = callback
        self._idcounter += 1

    def received_message(self, m):
        j = json.loads(str(m))
        if 'id' in j:
            self._callbacks.get(j['id'], lambda e, r: None)(j.get('error', None), j.get('result', None))
        elif 'method' in j:
            parts = j['method'].split('.')
            self._on_notification.fire(parts[0], parts[1], j.get('params', None))
