.. image:: ../artwork/logo.png
  :width: 200px
  :align: right

.. _installation:

Installation
============

Graphcat
--------

To install the latest stable version of Graphcat and its dependencies, use `pip`::

    $ pip install graphcat

... once it completes, you'll be able to use all of Graphcat's core features.

Visualization
-------------

If you want to visualize Graphcat network diagrams like the ones seen elsewhere
in this documentation, you'll need to install `Graphviz <https://graphviz.org>`_,
which can't be installed via pip.  If you use `Conda <https://docs.conda.io/en/latest/>`_
(which we strongly recommend), you can install it as follows::

    $ conda install graphviz

Once you have Graphviz, you can install Graphcat with the necessary dependencies::

    $ pip install graphcat[vis]

.. _documentation:

Documentation
-------------

We assume that you'll normally access this documentation online, but if you
want a local copy on your own computer, do the following:

First, you'll need the `pandoc <https://pandoc.org>`_ universal document
converter, which can't be installed with pip ... if you use `Conda <https://docs.conda.io/en/latest/>`_
(again, strongly recommended), you can install it with the following::

    $ conda install pandoc

Once you have pandoc, install Graphcat along with all of the dependencies needed to build the docs::

    $ pip install graphcat[doc]

Next, do the following to download a tarball to the current directory
containing all of the Graphcat source code, which includes the documentation::

    $ pip download graphcat --no-binary=:all: --no-deps

Now, you can extract the tarball contents and build the documentation (adjust the
following for the version you downloaded)::

    $ tar xzvf graphcat-1.0.4.tar.gz
    $ cd graphcat-1.0.4/docs
    $ make html
