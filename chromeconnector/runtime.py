class Runtime:
    domain = 'Runtime'

    def __init__(self, host, sendMessage, onNotification, vent):
        self.sendMessage = sendMessage
        self._vent = vent
        self._host = host
        self._currentScopeVariables = []
        n = lambda d, m, p: self.notification(m, p) if d != "Debugger" else None
        onNotification += n

    def notification(self, method, params):
        self._vent.fire(method, params)

    def send_command(self, method, params=None, callback=None):
        self.sendMessage(self.domain + '.' + method, params, callback)

    def get_current_scope_variables(self):
        return self._currentScopeVariables

    def get_properties(self, objectId):
        def handle_response(error, result):
            if not error:
                self._currentScopeVariables = result
                self._vent.fire('object_properties', result)
            else:
                self._vent.fire('error', error)

        self.send_command('getProperties', {
            "objectId": objectId,
            "ownProperties": True,
        }, handle_response)
