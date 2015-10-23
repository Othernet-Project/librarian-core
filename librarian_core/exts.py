"""
exts.py: App extension container

Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import functools
import logging


class ExtensionAlreadyExists(Exception):
    pass


class ExtensionNameUnavailable(Exception):
    pass


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
    def __init__(self, name, attrpath, parent, onfail):
        self.__name = name
        self.__attrpath = attrpath
        self.__parent = parent
        self.__onfail = onfail

    def __call__(self, *args, **kwargs):
        if self.__onfail is not Nothing:
            # a method was invoked on a non-existent extension with a
            # preconfigured value to be returned or exception raised, if the
            # extension indeed does not exist.
            if isinstance(self.__onfail, Exception):
                raise self.__onfail
            return self.__onfail
        # default behavior: store the called method name and params and return
        # the same ``Placeholder`` object to continue with the charade
        self.__parent.store_call(self.__name, self.__attrpath, args, kwargs)
        return self

    def __getattr__(self, attrname):
        # create a new ``Placeholder`` with the same configuration, just add
        # the nested attribute name to the exisiting name
        return Placeholder(self.__name,
                           '.'.join([self.__attrpath, attrname]),
                           self.__parent,
                           self.__onfail)


class ExtContainer(object):
    """Allows code which accesses pluggable extensions to still work even if
    the dependencies in question are not installed. Mainly meant to avoid
    putting boilerplate checks in such code to check for their existence.

    :param onfail: Value to be returned or exception to be raised by a
                   ``Placeholder`` if a method is invoked on a non-existent
                   extension.
    :param exts:   Used internally for cloning an ``ExtContainer`` object
    :param calls:  Used internally for cloning an ``ExtContainer`` object
    :param ignore: Used internally for cloning an ``ExtContainer`` object

    Usage:

    >>> ec = ExtContainer()
    >>> ec.missing.nested.method(1, 2, c=3)
    >>> ec.is_installed('missing')
    False
    >>> ec.missing = Missing()  # previously called methods will be replayed
    >>> ec.is_installed('missing')
    True
    >>> ec.this.works.without.errors()
    >>> ec(onfail=3).this.works.without.errors()
    3
    >>> err = Exception('test')
    >>> ec(onfail=err).this.works.without.errors()
    Traceback (most recent call last):
        ...
    Exception: test
    """
    _members = ('_extensions', '_onfail', '_calls', '_ignore')

    def __init__(self, onfail=Nothing, exts=None, calls=None, ignore=None):
        self._onfail = onfail
        self._extensions = exts or dict()
        self._calls = calls or dict()
        self._ignore = ignore or []

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
            return Placeholder(name=name,
                               attrpath='',
                               parent=self,
                               onfail=onfail)

    def __install_extension(self, name, extension):
        # protect against overwriting existing extensions
        if name in self._extensions:
            raise ExtensionAlreadyExists(name)
        # protect against using an extension name that is a valid attribute on
        # the parent container itself
        if name in dir(self):
            raise ExtensionNameUnavailable(name)

        self._extensions[name] = extension
        self.__replay_calls(name, extension)

    def __invoke(self, extension, attrpath, args, kwargs):
        attrs = [attr for attr in attrpath.split('.') if attr]
        try:
            method = functools.reduce(getattr, attrs, extension)
        except AttributeError:
            logging.error("Recorded calls on {0} cannot be replayed "
                          "retroactively.".format(attrpath))
        else:
            method(*args, **kwargs)

    def __replay_calls(self, name, extension):
        calls = self._calls.pop(name, None)
        if not calls:  # there were no registered calls, nothing to be done
            return

        # retroactively invoke all the methods on the actual extension
        for (attrpath, args, kwargs) in calls:
            self.__invoke(extension, attrpath, args, kwargs)

    def __getattr__(self, name):
        return self.__get_extension(name)

    def __setattr__(self, name, extension):
        # All assignments are delegated to the internal dict structure, unless
        # an existing attribute of the ``ExtContainer`` class is being assigned
        # e.g. as done in the constructor itself.
        if name in self._members:
            super(ExtContainer, self).__setattr__(name, extension)
        else:
            self.__install_extension(name, extension)

    __getitem__ = __getattr__
    __setitem__ = __setattr__

    def __call__(self, onfail):
        # re-create an ``ExtContainer`` with the same existing extensions, but
        # if methods are invoked on a non-existent extension, ``onfail`` will
        # be used as a return value, instead of another ``Placeholder`` object.
        return ExtContainer(onfail=onfail,
                            exts=self._extensions,
                            calls=self._calls,
                            ignore=self._ignore)

    def store_call(self, name, attrpath, args, kwargs):
        """Called by ``Placeholder`` objects to record calls to extension
        methods which will be replayed later when the extension is installed.
        """
        if name not in self._ignore:
            self._calls.setdefault(name, [])
            self._calls[name].append((attrpath, args, kwargs))

    def is_installed(self, name):
        """Check whether extension known by ``name`` is installed or not.

        :param name:  name of the extension that was supposedly installed
        """
        return name in self._extensions

    def flush(self, *extensions):
        """Delete the recorded calls for the specified extensions, or all calls
        if no specific names are provided.

        :param extensions:  names of extensions
        """
        names = extensions or list(self._calls.keys())
        for key in names:
            self._calls.pop(key, None)

    def ignore_calls_from(self, *extensions):
        """Add names of specified extensions to ignore list so no calls will be
        recorded for them while they are not installed.

        :param extensions:  names of extensions
        """
        self._ignore.extend(extensions)
