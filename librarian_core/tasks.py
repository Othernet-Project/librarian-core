import logging

import gevent


class TaskScheduler(object):

    def _execute(self, fn, args, kwargs):
        try:
            fn(*args, **kwargs)
        except Exception:
            logging.exception("Task execution failed.")

    def _periodic(self, fn, args, kwargs, delay):
        self._execute(fn, args, kwargs)
        gevent.spawn_later(delay, self._periodic, fn, args, kwargs, delay)

    def schedule(self, fn, args=None, kwargs=None, periodic=False, delay=None):
        delay = delay or 1
        args = args or tuple()
        kwargs = kwargs or dict()
        if periodic:
            gevent.spawn_later(delay, self._periodic, fn, args, kwargs, delay)
        else:
            gevent.spawn_later(delay, self._execute, fn, args, kwargs)

