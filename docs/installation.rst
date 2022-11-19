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

... once it completes, you'll be able to use all of Graphcat's features.

.. _documentation:

Documentation
-------------

We assume that you'll normally access this documentation online, but if you
want a local copy on your own computer, just do the following:

First, install Graphcat, along with all of the dependencies needed to build the docs::

    $ pip install graphcat[doc]

You'll also need the `pandoc <https://pandoc.org>`_ universal document
converter, which - regrettably - can't be installed with pip ... if you use
`Conda <https://docs.conda.io/en/latest/>`_ (which we strongly recommend), you
can install it easily::

    $ conda install pandoc

Next, do the following to download a tarball to the current directory
containing all of the Graphcat source code, including the documentation::

    $ pip download graphcat --no-binary=:all: --no-deps

Now, you can extract the tarball contents and build the source (adjust the
following for the version you downloaded)::

    $ tar xzvf graphcat-1.0.4.tar.gz
    $ cd graphcat-1.0.4/docs
    $ make html
