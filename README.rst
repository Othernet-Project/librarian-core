==============
librarian-core
==============

:master: |master-build|_ |master-coverage|
:develop: |develop-build|_ |develop-coverage|

.. |master-build| image:: https://travis-ci.org/Outernet-Project/librarian-core.svg?branch=master
.. _master-build: https://travis-ci.org/Outernet-Project/librarian-core
.. |develop-build| image:: https://travis-ci.org/Outernet-Project/librarian-core.svg?branch=develop
.. _develop-build: https://travis-ci.org/Outernet-Project/librarian-core
.. |master-coverage| image:: https://coveralls.io/repos/Outernet-Project/librarian-core/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/Outernet-Project/librarian-core?branch=master
.. |develop-coverage| image:: https://coveralls.io/repos/Outernet-Project/librarian-core/badge.svg?branch=develop&service=github
  :target: https://coveralls.io/github/Outernet-Project/librarian-core?branch=develop

A package providing a supervisor class that loosely ties together a couple of
abstract components which build upon the features of the base bottle_ framework
itself. Some of the tasks that this component-suite tries to solve are:

- static asset management
- authentication and authorization
- caching
- command line arguments
- database access
- internationalization
- session management
- background task execution
- signaling mechanism
- faster template rendering (built upon Mako_)

Due to the lack of any documentation at the moment, it is best to poke into the
source of other librarian-* components and see how this package is utilized by
them.

Installation
------------

The component has the following dependencies:

- bottle_
- bottle-utils_
- chainable-validators_
- cssmin_
- gevent_
- greentasks_
- Mako_
- pbkdf2_
- psycopg2_
- python-dateutil_
- pytz_
- squery-pg_
- webassets_


.. _bottle: http://bottlepy.org/
.. _bottle-utils: https://github.com/Outernet-Project/bottle-utils
.. _chainable-validators: https://github.com/Outernet-Project/chainable-validators
.. _cssmin: https://pypi.python.org/pypi/cssmin
.. _gevent: http://www.gevent.org/
.. _greentasks: https://github.com/Outernet-Project/greentasks 
.. _mako: http://www.makotemplates.org/
.. _pbkdf2: https://www.dlitz.net/software/python-pbkdf2/
.. _psycopg2: http://initd.org/psycopg/
.. _python-dateutil: https://pypi.python.org/pypi/python-dateutil
.. _pytz: https://pypi.python.org/pypi/pytz/
.. _squery-pg: https://github.com/Outernet-Project/squery-pg
.. _webassets: https://pypi.python.org/pypi/webassets
