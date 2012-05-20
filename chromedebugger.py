from config import *

class ChromeDebugger:
	domain = 'Debugger'

	def __init__(self, sendMessage, onNotification):
		self.sendMessage = sendMessage
		self.scripts = []
		self.set_breakpoints = dict()
		n = lambda d, m, p: self.notification(m, p) if d == self.domain else None
		onNotification += n

	def notification(self, method, params):
		if method == 'scriptParsed':
			if params['url'].find(host) >= 0:
				self.scripts.append(params)
		print method
		print params

	def enable(self):
		self.send_command('enable')

	def disable(self):
		self.send_command('disable')

	def resume(self):
		self.send_command('resume')

	def get_scriptId(self, url):
		r = -1
		for d in self.scripts: 
			if d['url'].find(url) > 0 and d['url'].find(host) >= 0: 
				r = d['scriptId']
		return r

	def send_command(self, method, params = None, callback = None):
		self.sendMessage(self.domain + '.' + method, params, callback)		

	def set_script_source(self, scriptId, newSource):
		self.send_command('setScriptSource', {
			"scriptId": scriptId,
			"scriptSource": newSource,
		}, self.set_script_source_result)

	def set_script_source_result(self, error, result):
		if not error:
			ct = result.get('result').get('change_tree')
			print ct

	def set_breakpoint(self, scriptId, line, condition=""):
		self.send_command('setBreakpoint', {
			"location": {
				"lineNumber": line,
				"scriptId": scriptId
			},
			"condition": condition,
		}, self.set_breakpoint_result)

	def set_breakpoint_result(self, error, result):
		if not error:
			print result

	def can_set_source(self):
		self.send_command('canSetScriptSource')		
