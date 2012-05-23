import sublime
import sublime_plugin
import json
import urllib2
from devtools import Session

SESSIONS = []
SETTINGS_FILE = "sublime-jslint.sublime-settings"
HOSTURL = '{0}:{1}'

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


class DetachAllCommand(sublime_plugin.WindowCommand):
    def run(self):
        while len(SESSIONS):
            SESSIONS.pop().kill()


class AttachToChromeCommand(sublime_plugin.WindowCommand):
    def run(self):
        while len(SESSIONS):
            SESSIONS.pop().kill()

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
                opts = [x for x in self.folders if not x is None]
                self.window.show_quick_panel(opts, self.onFolderPick)
            else:
                sublime.error_message(devToolsAttachedToTab)

    def onFolderPick(self, idx):
        folder = self.folders[idx]
        if idx >= 0 and not folder is None:
            SESSIONS.append(Session(self.window, folder, self.targetUrl))


class EventHandler(sublime_plugin.EventListener):
    def on_activated(self, view):
        if len(SESSIONS):
            filename = view.file_name()
            if filename:
                s = SESSIONS[0]
                sid = s.get_file_scriptId(filename)
                if sid > -1:
                    print 'Matched view to script ' + str(sid)
                    s.render_breakpoints(view)
                    s.render_pausemarks(view)

    def on_post_save(self, view):
        if len(SESSIONS):
            content = view.substr(sublime.Region(0, view.size()))
            SESSIONS[0].saved_file(view.file_name(), content)

    def on_load(self, view):
        self.on_activated(view)
