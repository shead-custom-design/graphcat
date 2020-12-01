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

"""Functionality for managing and executing computational graphs.
"""

__version__ = "0.9.0"

import collections
import enum
import functools
import logging
import time
import warnings

import blinker
import networkx

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


class StaticGraph(object):
    """Manages a static computational graph.

    The graph is a collection of named tasks, connected by links that define
    dependencies between tasks.  Updating a task implicitly updates all of its
    transitive dependencies.  When an unfinished task is updated, it executes a
    user-supplied function and stores the function return value as the task
    output.  Outputs of upstream tasks are automatically passed as inputs to
    downstream tasks.
    """
    def __init__(self):
        self._graph = networkx.MultiDiGraph()
        self._on_changed = blinker.Signal()
        self._on_execute = blinker.Signal()
        self._on_failed = blinker.Signal()
        self._on_finished = blinker.Signal()
        self._on_task_renamed = blinker.Signal()
        self._on_update = blinker.Signal()


    def __contains__(self, name):
        return name in self._graph


    def _require_valid_names(self, names):
        if names is None:
            return self.tasks()
        if not isinstance(names, (list, set)):
            names = [names]
        return {name for name in names if name in self._graph}


    def _require_task_present(self, name):
        if name not in self._graph:
            raise ValueError(f"Task {name!r} doesn't exist.")


    def _require_task_absent(self, name):
        if name in self._graph:
            raise ValueError(f"Task {name!r} already exists.")


    def add_links(self, source, targets):
        """Add links between `source` and `targets`.

        Parameters
        ----------
        source: hashable object, required
            Name of the task that will act as a data source.
        targets: tuple, or list of tuples, required
            Each (task, input) tuple specifies the target of a link.

        Raises
        ------
        :class:`ValueError`
            If `source` or `target` don't exist.
        """
        self._require_task_present(source)

        if not isinstance(targets, list):
            targets = [targets]

        # Add new edges
        unfinished = set()
        for target in targets:
            if isinstance(target, tuple):
                target, input = target
            else:
                input = None
            self._require_task_present(target)
            self._graph.add_edge(target, source, input=input) # Edges point from tasks to their dependencies.
            unfinished.add(target)

        self.mark_unfinished(unfinished)


    def add_task(self, name, fn=None):
        """Add a task to the graph.

        This function will raise an exception if the task already exists.

        See Also
        --------
        :meth:`set_task` : Modifies tasks, creating them if they don't already exist.

        Parameters
        ----------
        name: hashable object, required
            Unique label that will identify the task.
        fn: callable, optional
            The `fn` object will be called whenever the task is executed.  It must take two keyword arguments
            as parameters, `label` and `inputs`.  `name` will contain the unique task name.  `inputs` will
            be a dict mapping named inputs to a sequence of outputs returned from upstream tasks.
            If :any:`None` (the default), :func:`null` will be used.

        Raises
        ------
        :class:`ValueError`
            If `label` already exists.
        """
        self._require_task_absent(name)
        if fn is None:
            fn = null
        self.set_task(name, fn)


    def clear_links(self, source, target):
        """Remove links from the graph.

        This method will remove all links from `source` to `target`.

        Parameters
        ----------
        source: hashable object, required
            Source task name.
        target: hashable object, required
            Target task name.

        Raises
        ------
        :class:`ValueError`
            If `source` or `task` don't exist.
        """
        self._require_task_present(source)
        self._require_task_present(target)
        self.mark_unfinished(source)
        while self._graph.number_of_edges(target, source):
            self._graph.remove_edge(target, source)


    def clear_tasks(self, names=None):
        """Remove tasks from the graph, along with all related links.

        Note that downstream tasks will become unfinished.

        Parameters
        ----------
        names: :any:`None`, hashable object, or list|set of hashable objects, optional
            Names identifying the tasks to remove.  If :any:`None` (the default), all tasks are removed, emptying the graph.
        """
        names = self._require_valid_names(names)
        self.mark_unfinished(names)
        for name in names:
            self._graph.remove_node(name)
        self._on_changed.send(self)


    def links(self, names=None):
        """Return every link originating with the given names.

        Parameters
        ----------
        names: :any:`None`, hashable object, or list|set of hashable objects, optional
            Names identifying the source tasks from which to retrieve links.

        Returns
        -------
        links: :class:`list`
            (source, target, input) tuple for every link in the graph.
        """
        names = self._require_valid_names(names)

        results = []
        for target, source, input in self._graph.edges(data="input"):
            if source in names:
                results.append((source, (target, input)))
        return results


    def mark_failed(self, names=None):
        """Set the failed state for tasks and all downstream dependents.

        Normally, the failed state is set automatically by :meth:`update`.  This
        method is provided for callers who want to set the failed state in
        response to some outside event that the graph isn't aware of; this
        should only happen in extremely rare situations.

        Parameters
        ----------
        names: :any:`None`, hashable object, or list|set of hashable objects, required
            Task names to be marked as failed.  If :any:`None` (the default), all tasks are marked as failed.
        """
        names = self._require_valid_names(names)

        for name in list(names):
            for ancestor in networkx.ancestors(self._graph, name):
                names.add(ancestor)

        for name in names:
            self._graph.nodes[name]["output"] = None
            self._graph.nodes[name]["state"] = TaskState.FAILED

        self._on_changed.send(self)


    def mark_unfinished(self, names=None):
        """Set the unfinished state for tasks and all downstream dependents.

        Normally, the unfinished state is set automatically when changes are
        made to the graph.  This method is provided for callers who need to
        set the unfinished state in response to some outside event that the
        graph isn't aware of; this should only happen in extremely rare
        situations.

        Parameters
        ----------
        names: :any:`None`, hashable object, or list|set of hashable objects, required
            Task names to be marked as unfinished.  If :any:`None` (the default), the entire graph is marked unfinished.
        """
        names = self._require_valid_names(names)

        for name in list(names):
            for ancestor in networkx.ancestors(self._graph, name):
                names.add(ancestor)

        for name in names:
            self._graph.nodes[name]["output"] = None
            self._graph.nodes[name]["state"] = TaskState.UNFINISHED

        self._on_changed.send(self)


    @property
    def on_changed(self):
        """Signal emitted whenever a part of the graph becomes unfinished.

        Functions invoked by this signal must have the signature fn(graph),
        where `graph` is this object.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_changed


    @property
    def on_execute(self):
        """Signal emitted before a task is executed.

        Functions invoked by this signal must have the signature fn(graph, name, input),
        where `graph` is this object, `name` is the name of the task to be
        executed, and `input` is a dict containing the task inputs.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_execute


    @property
    def on_failed(self):
        """Signal emitted when a task fails during execution.

        Functions invoked by this signal must have the signature fn(graph, name, exception),
        where `graph` is this object, `name` is the name of the task that failed, and
        `exception` is the exception raised by the task.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_failed


    @property
    def on_finished(self):
        """Signal emitted when a task executes successfully.

        Functions invoked by this signal must have the signature fn(graph, name, output),
        where `graph` is this object, `name` is the name of the task that
        executed successfully, and `output` is the return value from the task
        function.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_finished


    @property
    def on_task_renamed(self):
        """Signal emitted when a task is renamed.

        Functions invoked by this signal must have the signature
        fn(graph, oldname, newname), where `graph` is this object, `oldname` is
        the original name of the task, and `newname` is its
        current name.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_task_renamed


    @property
    def on_update(self):
        """Signal emitted when a task is updated.

        Functions invoked by this signal must have the signature fn(graph, name),
        where `graph` is this object and `name` is the name of the task to be
        updated.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_update


    def output(self, name):
        """Retrieve the output from a task.

        This implicitly updates the graph, so the returned value is
        guaranteed to be up-to-date.

        Parameters
        ----------
        name: hashable object, required
            Unique task name.

        Returns
        -------
        output: any object
            The value returned when the task function was last executed, or :any:`None`.

        Raises
        ------
        :class:`ValueError`
            If `name` doesn't exist.
        :class:`Exception`
            Any exception raised by a task function will be re-raised by :meth:`output`.
        """
        self._require_task_present(name)
        self.update(name)
        return self._graph.nodes[name]["output"]


    def rename_task(self, oldname, newname):
        """Change an existing task's name.

        This modifies an existing task's name and modifies any related links
        as-necessary.  In addition, the task and any downstream dependents will
        become unfinished.

        Parameters
        ----------
        oldname: hashable object, required
            Existing original task name.
        newname: hashable object, required
            Unique new task name.

        Raises
        ------
        :class:`ValueError`
            If the task with `oldname` doesn't exist, or a task with `newname` already exists.
        """
        self._require_task_present(oldname)
        self._require_task_absent(newname)
        networkx.relabel_nodes(self._graph, mapping = {oldname: newname}, copy=False)
        self.mark_unfinished(newname)
        self._on_task_renamed.send(self, oldname=oldname, newname=newname)


    def set_expression(self, name, expression, locals={}):
        """Create a task that will execute a Python expression.

        The task will automatically track implicit dependencies that
        arise from executing the expression.

        Parameters
        ----------
        name: hashable object, required
            Unique name for the new expression task.
        expression: string, required
            Python expression that will be executed whenever the task is executed.
        locals: dict, optional
            Optional dictionary containing local objects that will be available for
            use in the expression.
        """
        fn = execute(expression, locals)
        fn = automatic_dependencies(fn)
        self.set_task(name, fn)


    def set_links(self, source, targets):
        """Set links between `source` and `targets`.

        .. note::

            This function overrides *all* links from `source`.

        Parameters
        ----------
        source: hashable object, required
            Name of the task that will act as a data source.
        targets: tuple, or list of tuples, required
            Each (task, input) tuple specifies the target of a link.

        Raises
        ------
        :class:`ValueError`
            If `source` or `target` don't exist.
        """
        self._require_task_present(source)

        if not isinstance(targets, list):
            targets = [targets]

        # Remove existing edges
        unfinished = set()
        for remove_target, remove_source in list(self._graph.in_edges(source)):
            self._graph.remove_edge(remove_target, remove_source)
            unfinished.add(remove_target)

        # Add new edges
        for target in targets:
            if isinstance(target, tuple):
                target, input = target
            else:
                input = None
            self._require_task_present(target)
            self._graph.add_edge(target, source, input=input) # Edges point from tasks to their dependencies.
            unfinished.add(target)

        self.mark_unfinished(unfinished)


    def set_parameter(self, target, input, source, value):
        """Create and link a 'parameter' task in one step.

        Because they're so ubiquitous, this method simplifies the creation of
        "parameter" tasks - tasks that return a value for use as a parameter in
        some other task.  It consolidates creating the parameter task and
        linking it with an existing computational task into one step.

        Parameters
        ----------
        target: hashable object, required
            Name of the task that will use the parameter.
        input: hashable object, required
            Named input that will receive the parameter.
        source: hashable object, required
            Name of the task that will store the parameter.
        value: any Python object, required
            Parameter value.

        Raises
        ------
        :class:`ValueError`
            If `target` doesn't exist.
        """
        self.set_task(source, constant(value))
        self.set_links(source, (target, input))


    def set_task(self, name, fn):
        """Add a task to the graph if it doesn't exist, and set its task function.

        Note that this will mark downstream tasks as unfinished.

        Parameters
        ----------
        name: hashable object, required
            Unique name that will identify the task.
        fn: callable, required
            The `fn` object will be called whenever the task is executed.  It must take two keyword arguments
            as parameters, `name` and `inputs`.  `name` will contain the unique task name.  `inputs` will
            be a dict mapping named inputs to sequences of outputs returned from upstream tasks.
        """
        if name in self._graph:
            self._graph.nodes[name]["fn"] = fn
        else:
            self._graph.add_node(name, fn=fn, state=TaskState.UNFINISHED, output=None)
        self.mark_unfinished(name)


    def state(self, name):
        """Return the current state of a task.

        Parameters
        ----------
        name: hashable object, required
            Unique name that identifies the task.

        Returns
        -------
        state: :class:`TaskState`
            Enumeration describing the current task state.

        Raises
        ------
        :class:`ValueError`
            If `name` doesn't exist.
        """
        self._require_task_present(name)
        return self._graph.nodes[name]["state"]


    def tasks(self):
        """Return the name of every task in the graph.

        Returns
        -------
        tasks: :class:`set`
            Names for every task in the graph.
        """
        return set(self._graph.nodes)


    def update(self, name):
        """Update a task and all its transitive dependencies.

        Parameters
        ----------
        name: hashable object, required
            Name identifying the task to be updated.

        Raises
        ------
        :class:`ValueError`
            If the task with `name` doesn't exist.
        :class:`Exception`
            Any exception raised by a task function will be re-raised by :meth:`update`.
        """

        self._require_task_present(name)

        # Keep track of failures.
        exception = None
        failed = None

        # Iterate over every task to be executed, in order ...
        for name in networkx.dfs_postorder_nodes(self._graph, name):
            task = self._graph.nodes[name]

            # Notify observers that the task will be updated.
            self._on_update.send(self, name=name)

            # Only execute this task if it isn't finished and a failure hasn't already occurred.
            if exception is None and task["state"] != TaskState.FINISHED:

                try:
                    # Gather inputs for the function.
                    inputs = collections.defaultdict(list)
                    for target, source, input in self._graph.out_edges(name, data="input"):
                        output = self._graph.nodes[source]["output"]
                        inputs[input].append(output)
                    inputs = dict(inputs)

                    # Execute the function and store the output.
                    self._on_execute.send(self, name=name, inputs=inputs)
                    task["output"] = task["fn"](graph=self, name=name, inputs=inputs)
                    task["state"] = TaskState.FINISHED
                    self._on_finished.send(self, name=name, output=task["output"])
                except Exception as e:
                    # The function raised an exception, notify observers.
                    exception = e
                    failed = name
                    self._on_failed.send(self, name=name, exception=e)

        # If a failure occurred, mark all downstream tasks.
        if failed is not None:
            self.mark_failed(failed)
            raise exception


class Graph(StaticGraph):
    """.. deprecated:: 0.9.0

    Use :class:`StaticGraph` instead.
    """
    def __init__(self):
        super().__init__()
        warnings.warn("graphcat.Graph is deprecated, use graphcat.StaticGraph instead.", DeprecationWarning, stacklevel=2)


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


def passthrough(input, index=0):
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


