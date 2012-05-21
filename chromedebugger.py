from config import *

class ChromeDebugger:
	domain = 'Debugger'

	def __init__(self, sendMessage, onNotification, vent):
		self.sendMessage = sendMessage
		self.scripts = []
		self.breakpoints = dict()
		self._vent = vent
		n = lambda d, m, p: self.notification(m, p) if d == self.domain else None
		onNotification += n

	def notification(self, method, params):
		if method == 'scriptParsed':
			if params['url'].find(host) >= 0:
				self.scripts.append(params)
		elif method == 'paused':
			self._vent.fire('paused', params)			
		print method

	def enable(self):
		self.send_command('enable')

	def disable(self):
		self.send_command('disable')

	def resume(self):
		self.send_command('resume')

	def step_over(self):
		self.send_command('stepOver')

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

	def set_breakpoint(self, scriptId, line, col=0, condition=""):
		def handle_response(error, result):
			if not error:
				self.breakpoints[result['breakpointId']] = result['actualLocation']
				self._vent.fire('breakpoints_changed', self.breakpoints)
			else: 
				self._vent.fire('error', error)			

		self.send_command('setBreakpoint', {
			"location": {
				"lineNumber": line,
				"columnNumber": col,
				"scriptId": scriptId
			},
			"condition": condition,
		}, handle_response)

	def remove_breakpoint(self, breakpointId):
		def handle_response(error, result):
			if not error:
				del self.breakpoints[breakpointId]
				self._vent.fire('breakpoints_changed', self.breakpoints)
			else:
				self._vent.fire('error', error)

		self.send_command('removeBreakpoint', {
			"breakpointId": breakpointId,
		}, handle_response)		

	def get_script_breakpoints(self, scriptId):
		r = []
		for v in self.breakpoints.itervalues():
			if v['scriptId'] == scriptId:
				r.append(v)
		return r

	def get_script_breakpoint_id(self, scriptId, line, col=0):
		for k, v in self.breakpoints.iteritems():
			print k, v
			if v['scriptId'] == str(scriptId) and v['lineNumber'] == (line):
				return k
		return None

	def can_set_source(self):
		self.send_command('canSetScriptSource')		
