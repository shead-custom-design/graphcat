# Copyright 2020 Timothy M. Shead
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Helpers that aren't specific to any one graph type.
"""

import collections
import enum
import functools
import logging
import time


log = logging.getLogger(__name__)


class DeprecationWarning(Warning):
    """Warning category for deprecated code."""
    pass


class Input(enum.Enum):
    """Enumerates special :class:`Graph` named inputs."""
    AUTODEPENDENCY = 1
    """Named input for links that are generated automatically for use as dependencies, not data sources."""


class Logger(object):
    """Log updates to the graph.

    Create a :class:`Logger` object to see the behavior of
    the graph during updates, using the Python :mod:`logging`
    module::

        logger = graphcat.Logger(graph)

    This is useful for debugging and pedagogy.  The logger will
    generate output for four types of event:

    * updated - called when a task is updated.
    * executed - called when a task is executed.
    * finished - called if a task executes successfully.
    * failed - called if a task raises an exception during execution.

    Update events happen regardless of the state of a task.  Execute events
    only happen if the task isn't already finished.

    Callers can derive from Logger and override :meth:`on_failed`,
    :meth:`on_finished`, :meth:`on_updated`, and :meth:`on_executed` to
    customize their behavior.

    Parameters
    ----------
    graph: class:`Graph`, required
        The graph whose events will be logged.
    """
    def __init__(self, graph, log_exceptions=True, log_inputs=True, log_outputs=True, log=log):
        self._log_exceptions = log_exceptions
        self._log_inputs = log_inputs
        self._log_outputs = log_outputs
        self._log = log

        graph.on_execute.connect(self.on_execute)
        graph.on_failed.connect(self.on_failed)
        graph.on_finished.connect(self.on_finished)
        graph.on_update.connect(self.on_update)

    def on_execute(self, graph, name, inputs):
        """Called when a task is executed."""
        if self._log_inputs:
            self._log.info(f"Task {name} executing. Inputs: {inputs}")
        else:
            self._log.info(f"Task {name} executing.")

    def on_failed(self, graph, name, exception):
        """Called when a task raises an exception during execution."""
        if self._log_exceptions:
            self._log.error(f"Task {name} failed. Exception: {exception}")
        else:
            self._log.error(f"Task {name} failed.")

    def on_finished(self, graph, name, output):
        """Called when a task has executed sucessfully."""
        if self._log_outputs:
            self._log.info(f"Task {name} finished. Output: {output}")
        else:
            self._log.info(f"Task {name} finished.")

    def on_update(self, graph, name):
        """Called when a task is updated."""
        self._log.debug(f"Task {name} updating.")


class PerformanceMonitor(object):
    """Tracks the performance of graph tasks as they're executed.

    Parameters
    ----------
    graph: :class:`Graph`, required
        Graph to watch for task execution.
    """
    def __init__(self, graph):
        self.reset()
        graph.on_execute.connect(self._on_execute)
        graph.on_failed.connect(self._on_failed)
        graph.on_finished.connect(self._on_finished)


    def _on_execute(self, graph, name, inputs):
        self._start = time.time()


    def _on_failed(self, graph, name, exception):
        self._tasks[name].append(time.time() - self._start) # pragma: no cover


    def _on_finished(self, graph, name, output):
        self._tasks[name].append(time.time() - self._start)


    def reset(self):
        """Clear performance data."""
        self._tasks = collections.defaultdict(list)


    @property
    def tasks(self):
        """Graph task execution times since this object was created / reset.

        Returns
        -------
        tasks: :class:`set`
            Python :class:`set` containing the names for every task that has
            been updated.
        """
        return dict(self._tasks)


class TaskState(enum.Enum):
    """Enumerates :class:`Graph` task states."""
    UNFINISHED = 1
    """The task is out-of-date and should be executed during the next update."""
    FAILED = 2
    """The task or one of it's dependencies failed during the last update."""
    FINISHED = 3
    """The task executed successfully during the last update."""


class UpdatedTasks(object):
    """Maintains a list of graph tasks that have been updated.

    Parameters
    ----------
    graph: :class:`Graph`, required
        Graph to watch for task updates.
    """
    def __init__(self, graph):
        self._tasks = set()
        graph.on_update.connect(self._on_update)

    def _on_update(self, graph, name):
        self._tasks.add(name)

    @property
    def tasks(self):
        """Graph tasks that have received updates since this object was created.

        Returns
        -------
        tasks: :class:`set`
            Python :class:`set` containing the names for every task that has
            been updated.
        """
        return self._tasks


def automatic_dependencies(fn):
    """Function decorator that automatically tracks dependencies.

    Use this to decorate task functions that need dependency tracking, such as
    :func:`execute`.

    See Also
    --------
    :meth:`Graph.set_expression`
        Convenience method that configures a task to evaluate expressions and
        automatically track dependencies.
    """
    @functools.wraps(fn)
    def implementation(graph, name, inputs):
        # Remove old, automatically generated dependencies.
        edges = list(graph._graph.out_edges(name, data="input", keys=True))
        for target, source, key, input in edges:
            if input == Input.AUTODEPENDENCY:
                graph._graph.remove_edge(target, source, key)

        # Keep track of dependencies while the task executes.
        updated = UpdatedTasks(graph)
        result = fn(graph, name, inputs)

        # Create new dependencies.
        sources = updated.tasks.difference([name])
        for source in sources:
            graph._graph.add_edge(name, source, input=Input.AUTODEPENDENCY)
        return result
    return implementation


def constant(value):
    """Factory for task functions that return constant values when executed.

    This is useful when creating a task that will act as a parameter
    for a downstream task::

        graph.add_task("theta", constant(math.pi))

    To change the parameter later, use :func:`constant` again, with
    :meth:`Graph.set_task_fn` to specify a new function::

        graph.set_task_fn("theta", constant(math.pi / 2))

    See Also
    --------
    :class:`Variable`: An alternate method for managing tasks as parameters.

    Parameters
    ----------
    value: any value, required
        The value to return when the task is executed.

    Returns
    -------
    fn: function
        Task function that will always return `value` when executed.
    """
    def implementation(graph, name, inputs):
        return value
    return implementation


def delay(seconds):
    """Factory for task functions that sleep for a fixed time.

    This is useful for testing and debugging.

    Parameters
    ----------
    seconds: number, required
        Number of seconds to sleep when executed.

    Returns
    -------
    fn: function
        Task function that will always sleep for `seconds` when executed.
    """
    def implementation(graph, name, inputs):
        time.sleep(seconds)
    return implementation


def execute(code, locals={}):
    """Factory for task functions that execute Python expressions.

    If your expressions can access the output from other tasks in the graph,
    you will want to use this function with the :func:`automatic_dependencies`
    decorator, or use :meth:`Graph.set_expression` which sets up dependency
    tracking for you.

    See Also
    --------
    :meth:`Graph.set_expression`
        Convenience method that configures a task to evaluate expressions and
        automatically track dependencies.

    Parameters
    ----------
    code: string, required
        Python code to be executed when the task is executed.
    locals: dict, optional
        Python dict containing local data that will be available
        to the expression when it's executed.

    Returns
    -------
    fn: function
        Task function that will execute Python code when the
        task is executed.
    """
    def implementation(graph, name, inputs):
        try:
            return eval(code, {}, dict(locals))
        except Exception as e: # pragma: no cover
            raise RuntimeError(f"Uncaught exception executing expression {code!r}: {e}")
    return implementation


def null(graph, name, inputs):
    """Task function that does nothing.

    This is the default if you don't specify a function for
    :meth:`Graph.add_task` or :meth:`Graph.set_task_fn`, and is useful in
    debugging and pedagogy.
    """
    pass


def passthrough(input=None, index=0):
    """Factory for task functions that pass-through incoming data.

    Callers can use this function to temporarily bypass tasks in the graph.

    Parameters
    ----------
    input: hashable object, required
        The named input that will pass-through to the task output.
    index: integer, required
        Index of the named inputs that will pass-through to the task output.

    Returns
    -------
    fn: function
        Task function that will pass input `input` index `index` to its output.
    """
    def implementation(graph, name, inputs):
        return inputs[input][index]
    return implementation


def raise_exception(exception):
    """Factory for task functions that raise an exception when executed.

    This is useful for debugging and pedagogy.

    Parameters
    ----------
    exception: :class:`BaseException` derivative, required
        The exception to raise when the task is executed.

    Returns
    -------
    fn: function
        Task function that will always raise `exception` when executed.
    """
    def implementation(graph, name, inputs):
        raise exception
    return implementation


