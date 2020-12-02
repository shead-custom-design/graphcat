.. image:: ../artwork/logo.png
  :width: 300px
  :align: right

Welcome!
========

Welcome to Graphcat ... the lightweight, flexible Python library for managing
computational graphs.

If you have a workflow composed of tasks, and the tasks need to be completed in
the right order, and the individual tasks are time-consuming so that you don't
want to execute a task unless it's really necessary, keeping track of which
tasks need to be executed can become extremely complex as your workflow grows,
branches, and merges.

Graphcat is a tool that allows you to explicitly capture this kind of workflow
in a *computational graph*, managing the details of executing each task in the
proper order and at the proper time, no matter the state of the graph or the
complexity of the workflow.  Graphcat doesn't care what kind of data your graph
manages, doesn't dictate how you name the entities in the graph, provides
advanced functionality like loops and expression-based tasks, and is easy to
learn, with features including the following:

* Tasks defined using standard Python functions or callables.
* No limitation on data structures / task outputs.
* Name tasks using any naming scheme you like.
* Support for advanced workflows including fan-in, fan-out, and loops.
* Built-in support for tasks based on Python expressions, with automatic dependency tracking.

Documentation
=============

.. toctree::
   :maxdepth: 2

   installation.rst
   dependencies.rst
   compatibility.rst
   contributing.rst
   tutorial.ipynb
   case-studies.rst
   projects.rst
   reference.rst
   support.rst
   release-notes.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

