.. image:: ../artwork/logo.png
  :width: 200px
  :align: right

.. _release-notes:

Release Notes
=============

Graphcat 0.7.0 - November 10, 2020
----------------------------------
* Breaking change: pass the graph as a parameter for task functions.
* Deprecated the graphcat.AutomaticDependencies class in favor of the graphcat.automatic_dependencies function decorator.

Graphcat 0.6.0 - November 8, 2020
---------------------------------
* Update dependencies every time an expression task executes.
* Handle automatic dependency tracking for tasks that are renamed.
* Deprecated graphcat.Graph.move_task() in favor of graphcat.Graph.rename_task().

Graphcat 0.5.0 - November 2, 2020
---------------------------------
* Make graphcat.notebook.display() output diagrams more compact.
* Add API to test whether the graph contains a task with a given name.
* Deprecated graphcat.ExpressionTask in favor of graphcat.Graph.set_expression().
* Clarify the graphcat.clear_links() documentation.
* Added graphcat.passthrough() for temporarily disabling tasks.

Graphcat 0.4.0 - October 15, 2020
---------------------------------
* Added graphcat.Graph.clear_links().
* graphcat.Graph.output() and graphcat.Graph.update() re-raise exceptions thrown by task functions.
* Allow parallel links between tasks.
* Deprecated graphcat.VariableTask.
* Added graphcat.Graph.set_parameter().

Graphcat 0.3.0 - October 11, 2020
---------------------------------
* Emit a signal when the graph is changed.
* Added an image processing use-case to the documentation.
* Refactor the API and deprecate add_relationship(), relabel_task(), remove_relationship(), remove_task(), set_input(), and set_task_fn().

Graphcat 0.2.0 - October 7, 2020
--------------------------------

* Fixed missing dependencies.
* Minor documentation tweaks.

Graphcat 0.1.0 - October 6, 2020
--------------------------------

* Initial Release
