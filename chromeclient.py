import json

from ws4py.client.threadedclient import WebSocketClient
from eventhook import EventHook
from chromedebugger import ChromeDebugger

class ChromeClient(WebSocketClient):
	def init(self):
		self.onNotification = EventHook()
		self.debugger = ChromeDebugger(self.send_message, self.onNotification)
		self.idcounter = 1
		self.callbacks = dict()

	def opened(self):
		print "Connection opened..."
		self.debugger.enable()
		self.debugger.can_set_source()

	def closed(self, code, reason=None):
		self.debugger.disable()
		print "Closed down", code, reason

	def send_message(self, method, params = None, callback = None):
		self.send(json.dumps({
			'id': self.idcounter, 
			'method': method,
			'params': params
		}))
		if callback: self.callbacks[self.idcounter] = callback
		self.idcounter += 1

	def received_message(self, m):
		j = json.loads(str(m))
		if j.has_key('id'):
			self.callbacks.get(j['id'], lambda e,r: None)(j.get('error', None), j.get('result', None))
		elif j.has_key('method'): 
			print j['method']
			parts = j['method'].split('.')
			self.onNotification.fire(parts[0], parts[1], j.get('params', None))