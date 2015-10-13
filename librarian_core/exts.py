"""
exts.py: App extension container

Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""


class Nothing(object):
    """Special object used to indicate that no return value is expected from
    the ``Placeholder`` object."""
    pass


class Placeholder(object):
    """Dummy object, returned by ``ExtContainer`` when non-existent extensions
    are accessed or methods are invoked on them.

    :param onfail: Value to be returned or exception to be raised if a method
                   is invoked.
    """
    def __init__(self, onfail):
        self.onfail = onfail

    def __call__(self, *args, **kwargs):
        if self.onfail is not Nothing:
            # a method was invoked on a non-existent extension with a
            # preconfigured value to be returned or exception raised, if the
            # extension indeed does not exist.
            if isinstance(self.onfail, Exception):
                raise self.onfail
            return self.onfail
        # default behavior, return a new ``Placeholder`` with the same config
        return Placeholder(self.onfail)

    def __getattr__(self, name):
        return Placeholder(self.onfail)


class ExtContainer(object):
    """Allows code which accesses pluggable extensions to still work even if
    the dependencies in question are not installed. Mainly meant to avoid
    putting boilerplate checks in such code to check for their existence.

    :param onfail: Value to be returned or exception to be raised by a
                   ``Placeholder`` if a method is invoked on a non-existent
                   extension.
    :param exts:   Used internally for re-creating an ``ExtContainer`` object
                   It is basically the ``dict`` which contains the registered
                   extensions.
    """
    _members = ('_extensions', '_onfail')

    def __init__(self, onfail=Nothing, exts=None):
        self._onfail = onfail
        self._extensions = exts or dict()

    def __get_extension(self, name):
        # ``object.__getattribute__`` must be used to avoid infinite loops by
        # recursively calling ``__getattr__``.
        # just like assignments, all get operations are delegated to the
        # internal dict structure. calling the getter methods is safe. even if
        # a non-existent member is accessed, ``ExtContainer`` will return a
        # ``Placeholder`` object.
        exts = object.__getattribute__(self, '_extensions')
        try:
            return exts[name]
        except KeyError:
            onfail = object.__getattribute__(self, '_onfail')
            return Placeholder(onfail)

    def __setattr__(self, name, extension):
        # All assignments are delegated to the internal dict structure, unless
        # an existing attribute of the ``ExtContainer`` class is being assigned
        # e.g. as done in the constructor itself.
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
        # re-create an ``ExtContainer`` with the same existing extensions, but
        # if methods are invoked on a non-existent extension, ``onfail`` will
        # be used as a return value, instead of another ``Placeholder`` object.
        return ExtContainer(onfail=onfail, exts=self._extensions)

    def is_installed(self, name):
        """Check whether extension known by ``name`` is installed or not.

        :param name:  name of the extension that was supposedly installed
        """
        return name in self._extensions
