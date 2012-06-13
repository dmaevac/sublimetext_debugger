import time
from threading import Timer
get_miliseconds = lambda: time.time() * 1000


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
