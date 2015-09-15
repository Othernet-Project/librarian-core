"""
tasks.py: Simple task scheduler and consumer

Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import logging
import Queue


class TaskScheduler(object):

    def __init__(self):
        self._tasks = Queue.Queue()

    def schedule(self, fn, *args, **kwargs):
        self._tasks.put((fn, args, kwargs))

    def consume(self):
        while True:
            try:
                (fn, args, kwargs) = self._tasks.get(block=False)
            except Queue.Empty:
                break
            else:
                try:
                    fn(*args, **kwargs)
                except Exception:
                    logging.exception("Task execution failed.")
