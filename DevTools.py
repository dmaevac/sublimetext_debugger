import sublime, sublime_plugin
import json
import pprint
import urllib2

from eventhook import EventHook
from chromeclient import ChromeClient
from config import *

class ResumeCommand(sublime_plugin.TextCommand):
	def run(self, edit):			
		s = sessions[0]
		s.resume()

	def is_enabled(self):
		return len(sessions) > 0 and sessions[0].paused

class StepOverCommand(sublime_plugin.TextCommand):
	def run(self, edit):			
		s = sessions[0]
		s.step_over()

	def is_enabled(self):
		return len(sessions) > 0 and sessions[0].paused

class ToggleBreakpointCommand(sublime_plugin.TextCommand):
	def run(self, edit):			
		s = sessions[0]
		p = self.view.full_line(self.view.sel()[0])
		rowcol = self.view.rowcol(p.begin())
		s.toggle_breakpoint(self.view.file_name(), rowcol[0], 0)

	def is_enabled(self):
		return len(sessions) > 0

class AttachToChromeCommand(sublime_plugin.WindowCommand):
	def run(self):
		while len(sessions):
			sessions.pop().kill()

		self.targets = dict()
		self.folders = self.window.folders()

		# TODO: Ensure at least one folder is added to project

		try:
			data = urllib2.urlopen(hostUrl.format(host, port) + '/json')
			self.targets = [x for x in json.load(data)]
			opts = [x["title"] for x in self.targets if x["title"][:17] != 'chrome-extension:']
			self.window.show_quick_panel(opts, self.onTargetPick)
		except urllib2.URLError, err:
			sublime.error_message(chromeNotRunningMessage.format(port))

	def onTargetPick(self, idx):
		if idx >= 0:
			if "webSocketDebuggerUrl" in self.targets[idx]:
				self.targetUrl = self.targets[idx]["webSocketDebuggerUrl"]
				opts = [x for x in self.folders if not x is None]
				self.window.show_quick_panel(opts, self.onFolderPick)
			else:
				sublime.error_message(devToolsAttachedToTab)			
		
	def onFolderPick(self, idx):
		folder = self.folders[idx]
		if idx >= 0 and not folder is None:	
			sessions.append(Session(self.window, folder, self.targetUrl))
	
class EventHandler(sublime_plugin.EventListener):
	def on_activated(self, view):
		if len(sessions):
			filename = view.file_name()
			if filename:
				s = sessions[0]
				sid = s.get_file_scriptId(filename)
				if sid > -1:
					s.render_breakpoints(view)

	def on_post_save(self, view):
		if len(sessions):
			content = view.substr(sublime.Region(0,view.size()))
			sessions[0].saved_file(view.file_name(), content)		


class Session():
	def __init__(self, window, folder, wsUrl):
		self.folder = fix_filename(folder)
		self._subwindow = window
		self.vent = EventHook()
		self.paused = False
		self.client = ChromeClient(wsUrl)
		self.client.init(self.vent)
		self.client.daemon = False
		self.client.connect()
		self.vent += self.on_vent

	def paused():
	    doc = "The paused property."
	    def fget(self):
	        return self._paused
	    def fset(self, value):
	        self._paused = value
	    def fdel(self):
	        del self._paused
	    return locals()
	paused = property(**paused())

	def on_vent(self, name, data):
		l = None
		if name == 'breakpoints_changed':
			l = lambda: self.render_breakpoints(self._subwindow.active_view())
		elif name == 'paused' and data:
			self.paused = True
			locations = [x["location"] for x in data['callFrames']]
			l = lambda: self.render_pausemarks(self._subwindow.active_view(), locations)
		elif name == 'resumed':
			self.paused = False	
			l = lambda: self._subwindow.active_view().erase_regions('pausemarks')
		if l:
			sublime.set_timeout(l,1)			
		print name

	def fix_filename(filename):
		# TODO: Do this properly - os.path
		return filename.replace('\\','/')

	def locations_to_regions(self, view, locations):
		regions = []
		for bp in locations:
			line = int(bp["lineNumber"]) 
			col = int(bp.get("columnNumber", 0)) 
			pos = view.text_point(line, col)
			reg = view.full_line(sublime.Region(pos,pos))
			regions.append(reg)
			print 'Location at', bp
		return regions

	# TODO: refactor the render_XYZ functions into a single render_marks

	def render_pausemarks(self, view, locations):
		regions = self.locations_to_regions(self._subwindow.active_view(), locations)
		view.add_regions('pausemarks', regions, 'pausemarks', 'circle')

	def render_breakpoints(self, view):
		scriptId = self.get_file_scriptId(view.file_name())
		breakpoints = self.client.debugger.get_script_breakpoints(scriptId)
		regions = self.locations_to_regions(view, breakpoints)
		view.add_regions('breakpoints', regions, 'breakpoints', 'dot')

	def get_file_scriptId(self, filename):
		if not filename is None:
			f = fix_filename(filename.replace(self.folder, ''))
			return self.client.debugger.get_scriptId(f)
		return -1

	def resume(self):
		self.client.debugger.resume()

	def step_over(self):
		self.client.debugger.step_over()

	def toggle_breakpoint(self, filename, line, col=0):
		scriptId = self.get_file_scriptId(filename)
		if scriptId > 0:	
			breakpointId = self.client.debugger.get_script_breakpoint_id(scriptId, line, col)
			if breakpointId is None:
				print 'Set BP at ', line, col
				self.client.debugger.set_breakpoint(scriptId, line, col)
			else:
				print 'Remove BP ', breakpointId
				self.client.debugger.remove_breakpoint(breakpointId)
		else:
			sublime.error_message(couldNotMatchFileToChrome)		

	def saved_file(self, filename, content):
		scriptId = self.get_file_scriptId(filename)
		if scriptId > 0:
			self.client.debugger.set_script_source(scriptId, content)

	def kill(self):
		self.client.close()
		print 'Session Killed'		
