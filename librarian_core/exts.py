"""
exts.py: App extension container

Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""


class Nothing(object):
    pass


class Placeholder(object):

    def __init__(self, onfail):
        self.onfail = onfail

    def __call__(self, *args, **kwargs):
        if self.onfail is not Nothing:
            if isinstance(self.onfail, Exception):
                raise self.onfail
            return self.onfail
        return Placeholder(self.onfail)

    def __getattr__(self, name):
        return Placeholder(self.onfail)


class ExtContainer(object):
    """Allows code which accesses pluggable extensions to still work even if
    the dependencies in question are not installed. Mainly meant to avoid
    putting boilerplate checks in such code to check for their existence.
    """
    _members = ('_extensions', '_onfail')

    def __init__(self, onfail=Nothing, exts=None):
        self._onfail = onfail
        self._extensions = exts or dict()

    def __get_extension(self, name):
        exts = object.__getattribute__(self, '_extensions')
        try:
            return exts[name]
        except KeyError:
            onfail = object.__getattribute__(self, '_onfail')
            return Placeholder(onfail)

    def __setattr__(self, name, extension):
        if name in self._members:
            super(ExtContainer, self).__setattr__(name, extension)
        else:
            self._extensions[name] = extension

    def __getattr__(self, name):
        return self.__get_extension(name)

    def __getitem__(self, name):
        return self.__get_extension(name)

    __setitem__ = __setattr__

    def __call__(self, onfail):
        return ExtContainer(onfail=onfail, exts=self._extensions)

    def is_installed(self, name):
        """Check whether extension known by `name` is installed or not."""
        return name in self._extensions
