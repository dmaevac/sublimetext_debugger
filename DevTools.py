import sublime, sublime_plugin
import json
import pprint
import urllib2

from chromeclient import ChromeClient
from config import *

class ToggleBreakpointCommand(sublime_plugin.TextCommand):
	def run(self, edit):			
		s = sessions[0]
		p = self.view.sel()[0].begin()
		rowcol = self.view.rowcol(p)
		s.toggle_breakpoint(self.view.file_name(), rowcol[0]+1)

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
		if idx >= 0 and not self.folders[idx] is None:	
			sessions.append(Session(self.folders[idx], self.targetUrl))
	
class EventHandler(sublime_plugin.EventListener):
	def on_activated(self, view):
		if len(sessions):
			sid = sessions[0].get_file_scriptId(view.file_name())
			if sid > -1:
				print 'Matched current view to script ' + sid

	def on_post_save(self, view):
		if len(sessions):
			content = view.substr(sublime.Region(0,view.size()))
			sessions[0].saved_file(view.file_name(), content)		

class Session():
	def __init__(self, folder, wsUrl):
		self.folder = folder
		self.client = ChromeClient(wsUrl)
		self.client.init()
		self.client.daemon = False
		self.client.connect()

	def get_file_scriptId(self, filename):
		if not filename is None:
			f = filename.replace(self.folder, '')
			return self.client.debugger.get_scriptId(f)
		return -1

	def toggle_breakpoint(self, filename, line):
		scriptId = self.get_file_scriptId(filename)
		if scriptId > 0:			
			self.client.debugger.set_breakpoint(scriptId, line)
		else:
			sublime.error_message(couldNotMatchFileToChrome)		

	def saved_file(self, filename, content):
		scriptId = self.get_file_scriptId(filename)
		if scriptId > 0:
			self.client.debugger.set_script_source(scriptId, content)

	def kill(self):
		self.client.close()
		print 'Session Killed'		
