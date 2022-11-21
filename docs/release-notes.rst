.. image:: ../artwork/logo.png
  :width: 200px
  :align: right

.. _release-notes:

Release Notes
=============

Graphcat 1.0.5 - November 20, 2022
----------------------------------

* Cleanup and organize documentation.
* Add numpy and pygraphviz as optional dependencies.

Graphcat 1.0.4 - November 18, 2022
----------------------------------

* Reduced the amount of boilerplate for optional functionality.
* Switched to pyproject.toml for packaging.
* Switched to flit for building.
* Minimum Python version is 3.8, due to upstream changes.
* Began testing with Python 3.11.
* Added optional dependencies for documentation and testing.

Graphcat 1.0.3 - October 21, 2021
---------------------------------

* Added a diagram filter for hiding "parameter" nodes.
* Added Python 3.10 to the CI build.
* Updated the way we collect code coverage data.
* Switched from Zulip to Github Discussions for support.

Graphcat 1.0.2 - October 13, 2021
---------------------------------

* Switched from Travis-CI to Github Actions for regression tests.
* Organized and streamlined the documentation.

Graphcat 1.0.1 - March 1, 2021
------------------------------

* Many documentation updates.
* Improve diagram edge label layout.

Graphcat 1.0.0 - February 2, 2021
---------------------------------

* First stable release of the Graphcat API!

Graphcat 0.13.0 - January 16, 2021
----------------------------------

* Fix a bug marking failed tasks in static graphs.
* Suppress unnecessary updates using graphcat.passthrough(), graphcat.delay(), and graphcat.raise_exception().
* Improve consistency throughout the regression test suite.
* Make it easier to display customized graph diagrams.
* Static graphs emit the on_cycle signal when a cycle is detected.
* Expose standard task function arguments in expressions, but give domain developers the ability to override or remove them.
* Expression tasks sometimes create redundant implicit dependencies.
* Deprecate graphcat.execute() in favor of graphcat.evaluate().

Graphcat 0.12.0 - December 19, 2020
-----------------------------------

* Expose the `rankdir` attribute when drawing graph diagrams.
* Alter graph diagram appearance based on graph type.
* Added a "User Guide" section to the documentation.
* Added graph.streaming.StreamingGraph.
* Greatly reduced code duplication among graph types.
* Calls to set_task() only mark the task unfinished if the new callable compares unequal to the old.
* Add support for visualizing performance data in graph diagrams.

Graphcat 0.11.0 - December 13, 2020
-----------------------------------

* Cycles are detected during dynamic graph updates.
* A new signal notifies callers when cycles occur.
* Static and dynamic graphs behave consistently when tasks fail.
* Moved graph drawing into a separate module, so callers can customize graph diagrams.
* Added graphcat.common.consume task function, for debugging dynamic graphs.
* Made pygraphviz an optional dependency, instead of required.
* Missing optional dependencies cause runtime failures, instead of failures at import.

Graphcat 0.10.0 - December 3, 2020
----------------------------------

* Introduced graphcat.DynamicGraph, which executes a computational graph with dynamic dependency checking.
* Introduced NamedInputs helpers to provide a cleaner / more consistent API for accessing task inputs.

Graphcat 0.9.0 - November 30, 2020
----------------------------------

* Deprecated graphcat.Graph, and added graphcat.StaticGraph instead.

Graphcat 0.8.0 - November 23, 2020
----------------------------------

* Added graphcat.PerformanceMonitor for evaluating task performance.
* graphcat.notebook.display() can optionally hide nodes that meet some criteria.
* Corrected typos in setup.py and release-notes.rst.

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

* Initial Release.
