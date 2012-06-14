import sublime
import datetime
import utils
import chromeconnector.client
import pystache
import pprint

reload(utils)
reload(chromeconnector.client)

SCOPE_VARS_NAME = 'Scope Variables'
SETTINGS_FILE = "sublime-jslint.sublime-settings"
couldNotMatchFileToChrome = 'Current file could not be found running in Chrome.'


def fix_filename(filename):
    # TODO: Do this properly - os.path
    return filename.replace('\\', '/')


def extended_view(view):
    def clear():
        edit = view.begin_edit()
        view.erase(edit, sublime.Region(0, view.size()))
        view.end_edit(edit)

    def replaceAll(text, point=0):
        edit = view.begin_edit()
        view.erase(edit, sublime.Region(0, view.size()))
        view.insert(edit, point, text)
        view.end_edit(edit)

    view.clear = clear
    view.replaceAll = replaceAll

    return view


class Session():
    def __init__(self, window, folder, wsUrl, websiteHost):
        s = sublime.load_settings(SETTINGS_FILE)
        host = s.get('host', 'http://localhost')

        self.folder = fix_filename(folder)
        self._subwindow = window
        self._host = websiteHost
        self._scopeView = None
        self.vent = utils.EventHook()
        # self.paused = False
        self.client = chromeconnector.client.ChromeClient(wsUrl)
        self.client.initialize(host, self.vent)
        self.client.daemon = False
        self.client.connect()
        self.vent += self.on_vent

    def paused():
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
            l = self.render_breakpoints
        elif name == 'paused' and data:
            self.paused = True
            l = self.focus_on_pausepoint
        elif name == 'resumed':
            self.paused = False
            l = self.render_pausemarks
        elif name == 'object_properties':
            l = self.render_scope_variables
        if l:
            sublime.set_timeout(lambda: l(self._subwindow.active_view(), data), 1)

        print datetime.datetime.now(), '[vented]', name

        if name == 'error':
            print name, data

    def locations_to_regions(self, view, scriptId, locations):
        regions = []
        for bp in (x for x in locations if x["scriptId"] == scriptId):
            line = int(bp["lineNumber"])
            col = int(bp.get("columnNumber", 0))
            pos = view.text_point(line, col)
            reg = view.full_line(sublime.Region(pos, pos))
            regions.append(reg)
        return regions

    def focus_on_pausepoint(self, currentView, data=None):
        pauselocations = self.client.debugger.get_script_pauselocations()
        if pauselocations:
            loc = pauselocations[0]
            scriptId = loc["scriptId"]
            filename = self.client.debugger.get_scriptFile(scriptId)
            filepath = self.folder + fix_filename(filename).replace(self._host, '')
            if fix_filename(currentView.file_name()) != filepath:
                print 'Opening ' + filepath
                self._subwindow.open_file(filepath)
            else:
                self.render_pausemarks(currentView)
                self.fetch_scope_variables(scriptId)

    def fetch_scope_variables(self, scriptId, query=None):
        # variables = self.client.runtime.get_current_scope_variables()
        cf = self.client.debugger.get_callFrames(scriptId)[0]
        oid = cf.get('scopeChain')[0]["object"].get('objectId')
        self.client.runtime.get_properties(oid)
        print 'Querying for ', scriptId, query

    def render_scope_variables(self, activeView, data=None):
        self._subwindow.set_layout({
            "cols": [0.0, 0.75, 1.0],
            "rows": [0.0, 1.0],
            "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
            })
        self._subwindow.focus_group(1)
        if self._scopeView is None:
            self._scopeView = extended_view(self._subwindow.new_file())
            self._scopeView.set_name(SCOPE_VARS_NAME)
            self._scopeView.set_scratch(True)
        else:
            self._subwindow.set_view_index(self._scopeView, 1, 0)
        self._subwindow.focus_group(0)

        pprint.pprint(data)
        tpl = '{{#result}}{{name}}:\t\t{{#value}}{{description}}{{/value}}\r\n{{/result}}'
        self._scopeView.set_read_only(False)
        self._scopeView.replaceAll(pystache.render(tpl, data))
        self._scopeView.set_read_only(True)

    def render_pausemarks(self, view, data=None):
        scriptId = self.get_file_scriptId(view.file_name())
        pauselocations = self.client.debugger.get_script_pauselocations()
        if pauselocations:
            regions = self.locations_to_regions(view, scriptId, pauselocations)
            view.add_regions('pausemarks', regions, 'storage', 'circle')
            view.show(regions[0])
        else:
            view.erase_regions('pausemarks')

    def breakpoint_list(self):
        return self.client.debugger.get_breakpoint_locations()

    def render_breakpoints(self, view, data=None):
        scriptId = self.get_file_scriptId(view.file_name())
        breakpoints = self.client.debugger.get_script_breakpoints(scriptId)
        regions = self.locations_to_regions(view, scriptId, breakpoints)
        view.add_regions('breakpoints', regions, 'string', 'dot')

    def get_file_scriptId(self, filename):
        if not filename is None:
            f = fix_filename(filename).replace(self.folder, '')
            return self.client.debugger.get_scriptId(f)
        return -1

    def call_stack_locations(self):
        return self.client.debugger.get_call_stack_locations()

    def resume(self):
        self.client.debugger.resume()

    def step_over(self):
        self.client.debugger.step_over()

    def step_into(self):
        self.client.debugger.step_into()

    def step_out(self):
        self.client.debugger.step_out()

    def toggle_breakpoint(self, filename, line, col=0):
        scriptId = self.get_file_scriptId(filename)
        if scriptId > 0:
            breakpointIds = self.client.debugger.get_script_breakpoint_ids(scriptId, line, col)
            if not len(breakpointIds):
                print 'Set BP at ', line, col
                self.client.debugger.set_breakpoint(scriptId, line, col)
            else:
                print 'Remove BP ', breakpointIds
                for bp in breakpointIds:
                    self.client.debugger.remove_breakpoint(bp)
        else:
            sublime.error_message(couldNotMatchFileToChrome)

    def remove_breakpoints(self, filename):
        scriptId = self.get_file_scriptId(filename)
        breakpointIds = self.client.debugger.get_script_breakpoint_ids(scriptId)
        for bp in breakpointIds:
            self.client.debugger.remove_breakpoint(bp)

    def saved_file(self, filename, content):
        scriptId = self.get_file_scriptId(filename)
        if scriptId > 0:
            self.client.debugger.set_script_source(scriptId, content)

    def kill(self):
        self.client.close()
        print 'Session Killed'
