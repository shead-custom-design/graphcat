.. image:: ../artwork/graphcat.png
  :width: 200px
  :align: right

.. _installation:

Installation
============

Using a Package Manager
-----------------------------

A package manager (conda, apt, yum, MacPorts, etc) should generally be your
first stop for installing Graphcat - it will make it easy to install Graphcat and
its dependencies, keep them up-to-date, and even (gasp!) uninstall them
cleanly.  If your package manager doesn't support Graphcat yet, drop them a line
and let them know you'd like them to add it!

If you're new to Python or unsure where to start, we strongly recommend taking
a look at :ref:`Anaconda <anaconda-installation>`, which the Graphcat developers
use during their day-to-day work.

.. toctree::
  :maxdepth: 2

  anaconda-installation.rst

Using Pip / Easy Install
------------------------

If your package manager doesn't support Graphcat, or doesn't have the latest
version, your next option should be Python setup tools like `pip`.  You can
always install the latest stable version of Graphcat and its required
dependencies using::

    $ pip install graphcat

... following that, you'll be able to use all of Graphcat's features.

.. _From Source:

From Source
-----------

Finally, if you want to work with the latest, bleeding-edge Graphcat goodness,
you can install it using the source code::

    $ git clone https://github.com/shead-custom-design/graphcat
    $ cd graphcat
    $ sudo python setup.py install

The setup script installs Graphcat's required dependencies and copies Graphcat into
your Python site-packages directory, ready to go.

