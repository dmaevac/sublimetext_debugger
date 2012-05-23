import json
from ws4py.client.threadedclient import WebSocketClient
import chromedebugger
import debugger.eventhook

reload(chromedebugger)
reload(debugger.eventhook)


class ChromeClient(WebSocketClient):
    def initialize(self, host, vent):
        self._on_notification = debugger.eventhook.EventHook()
        self.debugger = chromedebugger.ChromeDebugger(host, self.send_message, self._on_notification, vent)
        self.runtime = chromedebugger.ChromeRuntime(host, self.send_message, self._on_notification, vent)
        self.idcounter = 1
        self.callbacks = dict()

    def opened(self):
        print "Connection opened..."
        self.debugger.enable()
        self.debugger.can_set_source()

    def closed(self, code, reason=None):
        self.debugger.disable()
        print "Closed down", code, reason

    def send_message(self, method, params=None, callback=None):
        self.send(json.dumps({
            'id': self.idcounter,
            'method': method,
            'params': params
        }))
        if callback:
            self.callbacks[self.idcounter] = callback
        self.idcounter += 1

    def received_message(self, m):
        j = json.loads(str(m))
        if 'id' in j:
            self.callbacks.get(j['id'], lambda e, r: None)(j.get('error', None), j.get('result', None))
        elif 'method' in j:
            parts = j['method'].split('.')
            self._on_notification.fire(parts[0], parts[1], j.get('params', None))
