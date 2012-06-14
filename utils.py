import time
from threading import Timer
get_miliseconds = lambda: time.time() * 1000


class EventHook(object):

    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__handlers.remove(handler)
        return self

    def fire(self, *args, **keywargs):
        for handler in self.__handlers:
            handler(*args, **keywargs)

    def clearObjectHandlers(self, inObject):
        for theHandler in self.__handlers:
            if theHandler.im_self == inObject:
                self -= theHandler


class Throttle(object):
    def __init__(self, fn):
        def _func(a, t):
            fn(a)
            t.cancel()
        self.func = _func
        self.timer = None

    def __call__(self, arg):
        if not self.timer is None:
            self.timer.cancel()

        self.timer = Timer(2, self.func, [arg, self.timer])
        self.timer.start()

            # current_time = get_miliseconds()
            # # print current_time
            # # print self.last_call
            # # print current_time - self.last_call
            # if current_time - self.last_call > 2000:
            #     self.last_call = current_time
            #     self.callstack = []
            #     return self.func(*args, **kwargs)
