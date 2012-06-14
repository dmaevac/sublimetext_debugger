import sublime
import sublime_plugin
import json
import pprint
from urlparse import urlparse
import urllib2
import session
import utils

reload(session)
reload(utils)

SESSIONS = []
SETTINGS_FILE = "sublime-jslint.sublime-settings"
HOSTURL = '{0}:{1}'
SCOPE_VARS_NAME = 'Scope Variables'
CALL_STACK_NAME = 'Call Stack'

devToolsAttachedToTab = 'Developer tools are already connected to this tab. Please close and try again.'
chromeNotRunningMessage = 'Error connecting to Chrome. Ensure Chrome is running and that it has been started with the argument " --remote-debugging-port={0}"'
projectNotAttached = 'No projects are currently attached to Chrome. Use the Attach To Chrome command first.'


class ResumeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = SESSIONS[0]
        s.resume()

    def is_enabled(self):
        return len(SESSIONS) > 0 and SESSIONS[0].paused


class StepOverCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = SESSIONS[0]
        s.step_over()

    def is_enabled(self):
        return len(SESSIONS) > 0 and SESSIONS[0].paused


class StepIntoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = SESSIONS[0]
        s.step_into()

    def is_enabled(self):
        return len(SESSIONS) > 0 and SESSIONS[0].paused


class StepOutCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = SESSIONS[0]
        s.step_out()

    def is_enabled(self):
        return len(SESSIONS) > 0 and SESSIONS[0].paused


class ToggleBreakpointCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = SESSIONS[0]
        p = self.view.full_line(self.view.sel()[0])
        rowcol = self.view.rowcol(p.begin())
        s.toggle_breakpoint(self.view.file_name(), rowcol[0], 0)

    def is_enabled(self):
        return len(SESSIONS) > 0


class RemoveAllBreakpointsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = SESSIONS[0]
        s.remove_breakpoints(self.view.file_name())

    def is_enabled(self):
        return len(SESSIONS) > 0


class ShowBreakpointListCommand(sublime_plugin.WindowCommand):
    def run(self):
        s = SESSIONS[0]
        self.bp_list = []
        for x in s.breakpoint_list():
            bp = [x["fileName"]]
            bp.append(str(x["lineNumber"] + 1))
            self.bp_list.append(bp)
        self.window.show_quick_panel(self.bp_list, self.onTargetPick)

    def onTargetPick(self, idx):
        print self.bp_list[idx]

    def is_enabled(self):
        return len(SESSIONS) > 0


class ShowCallStackCommand(sublime_plugin.WindowCommand):
    def run(self):
        s = SESSIONS[0]
        self.bp_list = []
        for x in s.call_stack_locations():
            bp = [x["functionName"]]
            bp.append(x["fileName"] + ':' + (str(x["lineNumber"] + 1)))
            self.bp_list.append(bp)
        self.window.show_quick_panel(self.bp_list, self.onTargetPick)

    def onTargetPick(self, idx):
        print self.bp_list[idx]

    def is_enabled(self):
        return len(SESSIONS) > 0 and SESSIONS[0].paused


class DetachAllCommand(sublime_plugin.WindowCommand):
    def run(self):
        while len(SESSIONS):
            SESSIONS.pop().kill()

    def is_enabled(self):
        return len(SESSIONS) > 0


class AttachToChromeCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.run_command('detach_all')

        self.targets = dict()
        self.folders = self.window.folders()
        s = sublime.load_settings(SETTINGS_FILE)
        host = s.get('host', 'http://localhost')
        port = s.get('port', '9222')

        # TODO: Ensure at least one folder is added to project
        try:
            data = urllib2.urlopen(HOSTURL.format(host, port) + '/json')
            self.targets = [x for x in json.load(data)]
            opts = [x["title"] for x in self.targets if x["title"][:17] != 'chrome-extension:']
            self.window.show_quick_panel(opts, self.onTargetPick)
        except urllib2.URLError:
            sublime.error_message(chromeNotRunningMessage.format(port))

    def onTargetPick(self, idx):
        if idx >= 0:
            if "webSocketDebuggerUrl" in self.targets[idx]:
                self.targetUrl = self.targets[idx]["webSocketDebuggerUrl"]
                u = urlparse(self.targets[idx].get('url'))
                self.websiteHost = u.scheme + "://" + u.netloc
                opts = [x for x in self.folders if not x is None]
                self.window.show_quick_panel(opts, self.onFolderPick)
            else:
                sublime.error_message(devToolsAttachedToTab)

    def onFolderPick(self, idx):
        folder = self.folders[idx]
        if idx >= 0 and not folder is None:
            SESSIONS.append(session.Session(self.window, folder, self.targetUrl, self.websiteHost))

    def is_enabled(self):
        return len(SESSIONS) == 0


class EventHandler(sublime_plugin.EventListener):
    def on_activated(self, view):
        if len(SESSIONS) and not view.is_scratch():
            filename = view.file_name()
            if filename:
                s = SESSIONS[0]
                sid = s.get_file_scriptId(filename)
                if sid > -1:
                    print 'Matched view to script ' + str(sid)
                    # cf = self.client.debugger.get_callFrames(scriptId)[0]
                    # oid = cf.get('this').get('objectId')
                    # self.client.runtime.get_properties(oid)
                    # self.render_scope_variables()
                    s.render_breakpoints(view)
                    s.render_pausemarks(view)
        else:
            view.erase_regions('breakpoints')

    def on_post_save(self, view):
        if len(SESSIONS):
            content = view.substr(sublime.Region(0, view.size()))
            SESSIONS[0].saved_file(view.file_name(), content)

    def on_load(self, view):
        if not view.is_scratch():
            self.on_activated(view)

    def on_close(self, view):
        if view.name() == SCOPE_VARS_NAME:
            pass
            # close the watch group

    def on_selection_modified(self, view):
        # if len(SESSIONS) and not view.is_scratch():
        #     s = SESSIONS[0]
        #     filename = view.file_name()
        #     if filename and s.paused:
        #         sid = s.get_file_scriptId(filename)
        #         if sid > -1:
        #             s.fetch_scope_variables(view.substr(view.sel()[0]))
        #print view.substr(view.sel()[0])
        # sublime.set_timeout(debounced(view), 1)
        pass


class TestCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_quick_panel([['SCOUT.App.Content.Ext.extend.loadModule', 'Spafax.SCOUT.App.Content.js:110'],
            ['SCOUT.App.Main.Ext.extend.loadModule', 'Spafax.SCOUT.App.Main.js:174']], lambda a: a)
