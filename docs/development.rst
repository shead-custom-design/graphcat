.. image:: ../artwork/logo.png
  :width: 200px
  :align: right

.. _development:

Development
===========

Getting Started
---------------

If you haven't already, you'll want to get familiar with the Graphcat repository
at http://github.com/shead-custom-design/graphcat ... there, you'll find the Graphcat
source code, issue tracker, discussions, and wiki.

You'll need to install `Graphviz <https://graphviz.org>`_ and `pandoc <https://pandoc.org>`_,
neither of which can be installed via pip.  If you use `Conda <https://docs.conda.io/en/latest/>`_
(which we strongly recommend), you can install them as follows::

    $ conda install graphviz pandoc

Next, you'll need to install all of the extra dependencies needed for Graphcat development::

    $ pip install graphcat[all]

Then, you’ll be ready to obtain Graphcat’s source code and install it using
“editable mode”. Editable mode is a feature provided by pip that links the
Graphcat source code into the install directory instead of copying it ... that
way you can edit the source code in your git sandbox, and you don’t have to
keep re-installing it to test your changes::

$ git clone https://github.com/shead-custom-design/graphcat.git
$ cd graphcat
$ pip install --editable.

Versioning
----------

Graphcat version numbers follow the `Semantic Versioning <http://semver.org>`_ standard.

Coding Style
------------

The Graphcat source code follows the `PEP-8 Style Guide for Python Code <http://legacy.python.org/dev/peps/pep-0008>`_.

Running Regression Tests
------------------------

To run the Graphcat test suite, simply run `regression.py` from the
top-level source directory::

    $ cd graphcat
    $ python regression.py

The tests will run, providing feedback on successes / failures.

Test Coverage
-------------

When you run the test suite with `regression.py`, it also automatically
generates code coverage statistics.  To see the coverage results, open
`graphcat/.cover/index.html` in a web browser.

Building the Documentation
--------------------------

To build the documentation, run::

    $ cd graphcat/docs
    $ make html

Once the documentation is built, you can view it by opening
`graphcat/docs/_build/html/index.html` in a web browser.
