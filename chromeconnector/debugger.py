def handle_error_response(error, result):
    if error:
        print error


class Debugger:
    domain = 'Debugger'

    def __init__(self, host, sendMessage, onNotification, vent):
        self.sendMessage = sendMessage
        self._scripts = dict()
        self._vent = vent
        self._host = host
        self._breakpoints = dict()
        self._currentCallFrames = []
        onNotification += lambda d, m, p: self.notification(m, p) if d == self.domain else None

    def notification(self, method, params):
        if method == 'scriptParsed':
            params['local'] = params['url'].find(self._host) >= 0
            self._scripts[params['url']] = params
        elif method == 'paused':
            self._currentCallFrames = params['callFrames']
        elif method == 'resumed':
            self._currentCallFrames = []
        elif method == 'globalObjectCleared':
            self._scripts = dict()
            self._currentCallFrames = []
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
        r = []
        for k, v in self._scripts.iteritems():
            if v['url'].find(url) > 0 and v['url'].find(self._host) >= 0:
                r.append(v['scriptId'])
        if len(r) > 1:
            print 'To Many Results', r
        return r[0] if len(r) >= 1 else -1

    def get_scriptFile(self, scriptId):
        r = [v["url"] for k, v in self._scripts.iteritems() if v["scriptId"] == scriptId]
        if len(r) > 1:
            print 'To Many Results', r
        return r[0] if len(r) >= 1 else -1

    def set_script_source(self, scriptId, newSource):
        def handle_response(error, result):
            if not error:
                ct = result.get('result')
                pass
            else:
                self._vent.fire('error', error)

        self.send_command('setScriptSource', {
            "scriptId": scriptId,
            "scriptSource": newSource,
        }, handle_response)

    def set_breakpoint(self, scriptId, line, col=0, condition=""):
        def handle_response(error, result):
            if not error:
                self._breakpoints[result['breakpointId']] = result['actualLocation']
                self._vent.fire('breakpoints_changed', self._breakpoints)
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
                del self._breakpoints[breakpointId]
                self._vent.fire('breakpoints_changed', self._breakpoints)
            else:
                self._vent.fire('error', error)

        self.send_command('removeBreakpoint', {
            "breakpointId": breakpointId,
        }, handle_response)

    def get_breakpoint_locations(self):
        r = []
        for k, x in self._breakpoints.iteritems():
            r.append({
                "id": k,
                "lineNumber": x["lineNumber"],
                "fileName": self.get_scriptFile(x["scriptId"]),
            })
        return r

    def get_script_breakpoints(self, scriptId):
        r = [x for x in self._breakpoints.itervalues() if x['scriptId'] == scriptId]
        return r

    def get_script_pauselocations(self, scriptId=None):
        r = []
        pauselocations = [x["location"] for x in self._currentCallFrames]
        if scriptId:
            r = [x for x in pauselocations if x['scriptId'] == scriptId]
        else:
            r = pauselocations
        return r

    def get_script_breakpoint_ids(self, scriptId, line=None, col=None):
        bps = []
        for k, v in self._breakpoints.iteritems():
            if v['scriptId'] == str(scriptId) and (line is None or v['lineNumber'] == (line)):
                bps.append(k)
        return bps

    def get_callFrames(self, scriptId):
        cf = []
        for v in self._currentCallFrames:
            if v['location'].get('scriptId', None) == scriptId:
                cf.append(v)
        return cf

    def get_call_stack_locations(self):
        r = []
        for x in self._currentCallFrames:
            r.append({
                "id": x["callFrameId"],
                "functionName": x["functionName"],
                "fileName": self.get_scriptFile(x["location"]["scriptId"]),
                "lineNumber": x["location"]["lineNumber"]
            })
        return r
