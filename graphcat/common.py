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
import warnings

import networkx

try:
    import numpy
except: # pragma: no cover
    pass

import graphcat.require


log = logging.getLogger(__name__)


class Array(object):
    """Task function callable that always returns a caller-supplied array.

    See Also
    --------
    :func:`array`
    """
    def __init__(self, value):
        self._value = value

    def __call__(self, graph, name, inputs, extent=None):
        return self._value[extent] if extent is not None else self._value

    def __eq__(self, other):
        return type(self) is type(other) and numpy.all(self._value == other._value)


class ArrayExtent(object):
    """Convenience for creating :class:`Array` compatible streaming extents.

    To generate extents, use any numpy-compatible
    `indexing notation <https://numpy.org/doc/stable/reference/arrays.indexing.html>`_::

        extent = ArrayExtent[0:4096]
        extent = ArrayExtent[::2]
        extent = ArrayExtent[:, 0]
        ...

    These extents are compatible with :class:`Array`.
    """
    def __class_getitem__(cls, key):
        return key


class Constant(object):
    """Task function callable that always returns a caller-supplied value.

    See Also
    --------
    :func:`constant`
    """
    def __init__(self, value):
        self._value = value

    def __call__(self, graph, name, inputs, extent=None):
        return self._value

    def __eq__(self, other):
        return type(self) is type(other) and self._value == other._value


class Delay(object):
    """Task function callable that sleeps for a fixed time.

    This is mainly useful for testing and debugging.

    See Also
    --------
    :func:`delay`
    """ 
    def __init__(self, seconds):
        self._seconds = seconds

    def __call__(self, graph, name, inputs, extent=None):
        time.sleep(self._seconds)

    def __eq__(self, other):
        return type(self) is type(other) and self._seconds == other._seconds


class DeprecationWarning(Warning):
    """Warning category for deprecated code."""
    pass


class Input(enum.Enum):
    """Enumerates special :class:`Graph` named inputs."""
    IMPLICIT = 1
    """Named input for links that are generated automatically for use as implicit dependencies, not data sources."""


class Logger(object):
    """Log graph events.

    Create a :class:`Logger` object to see the behavior of
    the graph during updates, using the Python :mod:`logging`
    module::

        logger = graphcat.Logger(graph)

    This is useful for debugging and pedagogy.  The logger will
    generate output for four types of event:

    * updated - called when a task is updated.
    * cycle - called when a cycle is detected during updating.
    * executed - called when a task is executed.
    * finished - called if a task executes successfully.
    * failed - called if a task raises an exception during execution.

    Update events happen regardless of the state of a task.  Execute events
    only happen if the task isn't already finished.

    Parameters
    ----------
    graph: class:`Graph`, required
        The graph whose events will be logged.
    """
    def __init__(self, graph, log_exceptions=True, log_inputs=True, log_outputs=True, log_extents=True, log=log):
        self._log_exceptions = log_exceptions
        self._log_inputs = log_inputs
        self._log_outputs = log_outputs
        self._log_extents = log_extents
        self._log = log

        graph.on_cycle.connect(self.on_cycle)
        graph.on_execute.connect(self.on_execute)
        graph.on_failed.connect(self.on_failed)
        graph.on_finished.connect(self.on_finished)
        graph.on_update.connect(self.on_update)


    def on_cycle(self, graph, name):
        """Called when a cycle is detected."""
        self._log.info(f"Task {name} cycle detected.")

    def on_execute(self, graph, name, inputs, extent=None):
        """Called when a task is executed."""
        message = f"Task {name} executing."
        if self._log_inputs:
            message += f" Inputs: {inputs}"
        if self._log_extents and graph.is_streaming:
            message += f" Extent: {extent}"
        self._log.info(message)

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
        message = f"Task {name} updating."
        self._log.info(message)


class Passthrough(object):
    """Task function callable that always returns an upstream input.

    See Also
    --------
    :func:`passthrough`
    """
    def __init__(self, input):
        self._input = input

    def __call__(self, graph, name, inputs, extent=None):
        return inputs.getone(self._input)

    def __eq__(self, other):
        return type(self) is type(other) and self._input == other._input


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


    def _on_execute(self, graph, name, inputs, extent=None):
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


class RaiseException(object):
    """Task function callable that always raises an exception.

    This is mainly useful for testing and debugging.

    See Also
    --------
    :func:`raise_exception`
    """
    def __init__(self, exception):
        self._exception = exception

    def __call__(self, graph, name, inputs, extent=None):
        raise self._exception

    def __eq__(self, other):
        return type(self) is type(other) and self._exception == other._exception


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


graphcat.require.loaded_module("numpy")
def array(value):
    """Factory for task functions that return constant array values when executed.

    Note
    ----
    This callable is designed to be compatible with :class:`ArrayExtent` extents
    when used in a :class:`graphcat.streaming.StreamingGraph`.

    Parameters
    ----------
    value: :class:`numpy.ndarray`-convertable value, required
        The array to return when the task is executed.

    Returns
    -------
    fn: :class:`Array`
        Task function that will always return `value` when executed.
    """
    return Array(value)


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
    def implementation(graph, name, inputs, extent=None):
        # Remove old implicit dependencies.
        edges = list(graph._graph.out_edges(name, data="input", keys=True))
        for target, source, key, input in edges:
            if input == Input.IMPLICIT:
                graph._graph.remove_edge(target, source, key)

        # Keep track of all dependencies while the task executes.
        updated = UpdatedTasks(graph)
        result = fn(graph, name, inputs, extent)

        # Filter out dependencies that are already explicitly captured.
        dependencies = updated.tasks
        dependencies = dependencies.difference(networkx.descendants(graph._graph, name))
        dependencies = dependencies.difference([name])

        # Create new implicit dependencies with what remains.
        for source in dependencies:
            graph._graph.add_edge(name, source, input=Input.IMPLICIT)

        return result
    return implementation


def builtins(graph, name, inputs, extent=None):
    """Returns standard builtin symbols for expression tasks:

    :graph: The :class:`graphcat.graph.Graph` executing the task.
    :name: Unique name of the task being executed.
    :inputs: Named inputs for the task being executed.
    :extent: Optional extent object for streaming graphs.

    """
    return {
        "graph": graph,
        "name": name,
        "inputs": inputs,
        "extent": extent,
    }


def constant(value):
    """Factory for task functions that return constant values when executed.

    This is useful when creating a task that will act as a parameter
    for a downstream task::

        graph.add_task("theta", constant(math.pi))

    To change the parameter later, use :func:`constant` again, with
    :meth:`Graph.set_task_fn` to specify a new function::

        graph.set_task_fn("theta", constant(math.pi / 2))

    Parameters
    ----------
    value: any value, required
        The value to return when the task is executed.

    Returns
    -------
    fn: :class:`Constant`
        Task function that will always return `value` when executed.
    """
    return Constant(value)


def consume(graph, name, inputs, extent=None):
    """Task function that retrieves all its inputs, but otherwise does nothing.

    This is mainly useful for debugging :class:`dynamic graphs<graphcat.dynamic.DynamicGraph>`,
    since the default :func:`null` task function won't execute upstream nodes.
    """
    values = [value() for value in inputs.values()]


def delay(seconds):
    """Factory for task functions that sleep for a fixed time.

    This is mainly useful for testing and debugging.

    Parameters
    ----------
    seconds: number, required
        Number of seconds to sleep when executed.

    Returns
    -------
    fn: function
        Task function that will always sleep for `seconds` when executed.
    """
    return Delay(seconds)


def evaluate(code, symbols=None):
    """Factory for task functions that evaluate Python expressions.

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
    symbols: callable, optional
        Function that returns a Python dict containing symbols that will be
        available to the expression when it's executed.  If :any:`None` (the
        default), the :func:`builtins` function will be used, which gives the
        expression access to `graph`, `name`, `inputs`, and `extent` objects
        that match the arguments to a normal task function.

    Returns
    -------
    fn: function
        Task function that will execute Python code when the
        task is executed.
    """
    if symbols is None:
        symbols = builtins

    def implementation(graph, name, inputs, extent=None):
        try:
            return eval(code, {}, symbols(graph, name, inputs, extent))
        except Exception as e: # pragma: no cover
            raise RuntimeError(f"Uncaught exception executing expression {code!r}: {e}")
    return implementation


def null(graph, name, inputs, extent=None):
    """Task function that does nothing.

    This is the default if you don't specify a function for
    :meth:`Graph.add_task` or :meth:`Graph.set_task_fn`, and is useful in
    debugging and pedagogy.
    """
    pass


def passthrough(input=None):
    """Factory for task functions that pass-through incoming data.

    Callers can use this function to temporarily bypass tasks in the graph.

    Parameters
    ----------
    input: hashable object, required
        The named input that will pass-through to the task output.

    Returns
    -------
    fn: function
        Task function that will pass the input value named `input` to its output.
    """
    return Passthrough(input)


def raise_exception(exception):
    """Factory for task functions that raise an exception when executed.

    This is mainly useful for testing and debugging.

    Parameters
    ----------
    exception: :class:`BaseException` derivative, required
        The exception to raise when the task is executed.

    Returns
    -------
    fn: function
        Task function that will always raise `exception` when executed.
    """
    return RaiseException(exception)

