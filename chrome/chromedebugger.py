def handle_error_response(error, result):
    if error:
        print error


class ChromeRuntime:
    domain = 'Runtime'

    def __init__(self, host, sendMessage, onNotification, vent):
        self.sendMessage = sendMessage
        self.scripts = []
        self._vent = vent
        self._host = host
        n = lambda d, m, p: self.notification(m, p) if d == self.domain else None
        onNotification += n

    def notification(self, method, params):
        if method == 'scriptParsed':
            if params['url'].find(self._host) >= 0:
                self.scripts.append(params)

    def send_command(self, method, params=None, callback=None):
        self.sendMessage(self.domain + '.' + method, params, callback)

    def get_properties(self, objectId):
        def handle_response(error, result):
            if not error:
                self._vent.fire('object_properties', result)
            else:
                self._vent.fire('error', error)

        self.send_command('getProperties', {
            "objectId": objectId,
            "ownProperties": True,
        }, handle_response)


class ChromeDebugger:
    domain = 'Debugger'

    def __init__(self, host, sendMessage, onNotification, vent):
        self.sendMessage = sendMessage
        self.scripts = []
        self._vent = vent
        self._host = host
        self.breakpoints = dict()
        self.currentCallFrames = []
        n = lambda d, m, p: self.notification(m, p) if d == self.domain else None
        onNotification += n

    def notification(self, method, params):
        if method == 'scriptParsed':
            if params['url'].find(self._host) >= 0:
                self.scripts.append(params)
        elif method == 'paused':
            self.currentCallFrames = params['callFrames']
            self._vent.fire(method, params)
        elif method == 'resumed':
            self.currentCallFrames = []
            self._vent.fire(method, params)
        elif method == 'breakpointResolved':
            self._vent.fire(method, params)

    def send_command(self, method, params=None, callback=None):
        self.sendMessage(self.domain + '.' + method, params, callback)

    def enable(self):
        self.send_command('enable', None, handle_error_response)

    def disable(self):
        self.send_command('disable', None, handle_error_response)

    def resume(self):
        self.send_command('resume', None, handle_error_response)

    def step_over(self):
        self.send_command('stepOver', None, handle_error_response)

    def step_into(self):
        self.send_command('stepInto', None, handle_error_response)

    def step_out(self):
        self.send_command('stepOut', None, handle_error_response)

    def can_set_source(self):
        self.send_command('canSetScriptSource', None, handle_error_response)

    def get_scriptId(self, url):
        r = -1
        for d in self.scripts:
            if d['url'].find(url) > 0 and d['url'].find(self._host) >= 0:
                r = d['scriptId']
        return r

    def get_scriptFile(self, scriptId):
        r = None
        for d in self.scripts:
            if d['scriptId'] == scriptId:
                return d["url"]
        return r

    def set_script_source(self, scriptId, newSource):
        def handle_response(error, result):
            if not error:
                ct = result.get('result').get('change_tree')
                print ct
            else:
                self._vent.fire('error', error)

        self.send_command('setScriptSource', {
            "scriptId": scriptId,
            "scriptSource": newSource,
        }, handle_response)

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

    def get_script_pauselocations(self, scriptId=None):
        r = []
        pauselocations = [x["location"] for x in self.currentCallFrames]
        if scriptId:
            r = [x for x in pauselocations if x['scriptId'] == scriptId]
        else:
            r = pauselocations
        return r

    def get_script_breakpoint_ids(self, scriptId, line=None, col=None):
        bps = []
        for k, v in self.breakpoints.iteritems():
            if v['scriptId'] == str(scriptId) and (line is None or v['lineNumber'] == (line)):
                bps.append(k)
        return bps

    def get_callFrames(self, scriptId):
        cf = []
        for v in self.currentCallFrames:
            if v['location'].get('scriptId', None) == scriptId:
                cf.append(v)
        return cf
