tsuru-circus
============

.. image:: https://secure.travis-ci.org/tsuru/tsuru-circus.png
   :target: http://travis-ci.org/tsuru/tsuru-circus


tsuru-circus is a collection of circus extensions for tsuru.

Installation
------------

::

    $ pip install tsuru-circus

Usage
-----

To use the tsuru stream to send circus log to tsuru you need to set the tsuru Stream in the circus conf:

::

    stderr_stream.class = tsuru.stream.Stream

development
===========

* Source hosted at `GitHub <http://github.com/tsuru/tsuru-circus>`_
* Report issues on `GitHub Issues <http://github.com/tsuru/tsuru-circus/issues>`_

Pull requests are very welcomed! Make sure your patches are well tested.

running the tests
-----------------

::

    $ python setup.py test

community
=========

irc channel
-----------

#tsuru channel on irc.freenode.net

LICENSE
=======

Unless otherwise noted, the tsuru-circus source files are distributed under the BSD-style license found in the LICENSE file.
