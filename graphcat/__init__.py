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

__version__ = "0.3.0"

import enum
import functools
import logging
import warnings

import blinker
import networkx

log = logging.getLogger(__name__)


class DeprecationWarning(Warning):
    """Warning category for deprecated code."""
    pass


class ExpressionTask(object):
    """Manage a task that executes Python expressions and tracks implicit dependencies.

    Parameters
    ----------
    graph: class:`Graph`, required
        The graph where the new expression task will be created.
    name: hashable object, required
        Unique name for the new expression task.
    expression: string, required
        Python expression that will be executed whenever the task is executed.
    locals: dict, optional
        Optional dictionary containing local objects that will be available for
        use in the expression.
    """
    def __init__(self, graph, name, expression, locals={}):
        self._graph = graph
        self._name = name
        self.set(expression, locals)

    def set(self, expression, locals={}):
        """Change the Python expression to be executed.

        Parameters
        ----------
        expression: string, required
            New Python expression that will be executed whenever the task is executed.
        locals: dict, optional
            Optional dictionary containing local objects that will be available for
            use in the expression.
        """
        self._graph.set_task(self._name, execute(expression, locals))

        sources = list(self._graph._graph.successors(self._name))
        for source in sources:
            self._graph._graph.remove_edge(self._name, source)

        updated = UpdatedTasks(self._graph)
        self._graph.update(self._name)

        sources = updated.tasks.difference([self._name])
        for source in sources:
            self._graph._graph.add_edge(self._name, source, input=Input.DEPENDENCY)


class Graph(object):
    """Manages a computational graph.

    The graph is a collection of named tasks, connected by links that define
    dependencies between tasks.  Updating a task implicitly updates all of its
    transitive dependencies.  When an unfinished task is updated, it executes a
    user-supplied function and stores the function return value as the task
    output.  Outputs of upstream tasks are automatically passed as inputs to
    downstream tasks.
    """
    def __init__(self):
        self._graph = networkx.DiGraph()
        self._on_changed = blinker.Signal()
        self._on_execute = blinker.Signal()
        self._on_failed = blinker.Signal()
        self._on_finished = blinker.Signal()
        self._on_update = blinker.Signal()


    def _require_valid_names(self, names):
        if names is None:
            return self.tasks()
        if not isinstance(names, (list, set)):
            names = [names]
        return {name for name in names if name in self._graph}


    def _require_task_present(self, name):
        if name not in self._graph:
            raise ValueError(f"Task {name} doesn't exist.")


    def _require_task_absent(self, name):
        if name in self._graph:
            raise ValueError(f"Task {name} already exists.")


    def _require_link_present(self, source, target):
        if self._graph.number_of_edges(target, source) != 1:
            raise ValueError(f"Edge {source} -> {target} doesn't exist.")


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


    def add_relationship(self, source, target, input=None):
        """.. deprecated:: 0.3.0

            Use :meth:`add_links` or :meth:`set_links` instead.
        """
        warnings.warn("graphcat.Graph.add_relationship is deprecated, use graphcat.Graph.add_links or graphcat.Graph.set_links instead.", DeprecationWarning, stacklevel=2)
        self._require_task_present(source)
        self._require_task_present(target)
        self._graph.add_edge(target, source, input=input) # Edges point from tasks to their dependencies.
        self.mark_unfinished(target)


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


    def clear_tasks(self, names=None):
        """Remove tasks from the graph, along with all related links.

        Note that downstream tasks will become unfinished.

        Parameters
        ----------
        names: :any:`None`, hashable object, or list|set of hashable objects, optional
            Names identifying the tasks to remove.  If any:`None` (the default), all tasks are removed, emptying the graph.
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

        result = []
        for target, source in self._graph.edges():
            if source in names:
                result.append((source, (target, self._graph.edges[(target, source)]["input"])))
        return result


    def mark_failed(self, names=None):
        """Set the failed state for tasks and all downstream dependents.

        Normally, the failed state is set automatically by :meth:`update`.  This
        method is provided for callers who want to set the failed state in
        response to some outside event that the graph isn't aware of; this
        should only happen in extremely rare situations.

        Parameters
        ----------
        names: :any:`None`, hashable object, or list|set of hashable objects, required
            Task names to be marked as failed.  If any:`None` (the default), all tasks are marked as failed.
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
            Task names to be marked as unfinished.  If any:`None` (the default), the entire graph is marked unfinished.
        """
        names = self._require_valid_names(names)

        for name in list(names):
            for ancestor in networkx.ancestors(self._graph, name):
                names.add(ancestor)

        for name in names:
            self._graph.nodes[name]["output"] = None
            self._graph.nodes[name]["state"] = TaskState.UNFINISHED

        self._on_changed.send(self)


    def move_task(self, oldname, newname):
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


    @property
    def on_changed(self):
        """Signal emitted whenever a part of the graph becomes unfinished.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_changed


    @property
    def on_execute(self):
        """Signal emitted before a task is executed.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_execute


    @property
    def on_failed(self):
        """Signal emitted when a task fails during execution.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_failed


    @property
    def on_finished(self):
        """Signal emitted when a task executes successfully.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_finished


    @property
    def on_update(self):
        """Signal emitted when a task is updated.

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
            The value returned when the task function was last executed, or any:`None`.

        Raises
        ------
        :class:`ValueError`
            If `name` doesn't exist.
        """
        self._require_task_present(name)
        self.update(name)
        return self._graph.nodes[name]["output"]


    def relabel_task(self, oldname, newname):
        """.. deprecated:: 0.3.0

            Use :meth:`move_task` instead.
        """
        warnings.warn("graphcat.Graph.relabel_task is deprecated, use graphcat.Graph.move_task instead.", DeprecationWarning, stacklevel=2)
        self.move_task(oldname, newname)


    def remove_relationship(self, source, target):
        """.. deprecated:: 0.3.0

            Use :meth:`clear_links` instead.
        """
        warnings.warn("graphcat.Graph.remove_relationship is deprecated, use graphcat.Graph.clear_links instead.", DeprecationWarning, stacklevel=2)
        self._require_task_present(source)
        self._require_task_present(target)
        self._require_link_present(source, target)
        self.mark_unfinished(source)
        self._graph.remove_edge(target, source)


    def remove_task(self, name):
        """.. deprecated:: 0.3.0

            Use :meth:`clear_tasks` instead.
        """
        warnings.warn("graphcat.Graph.remove_task is deprecated, use graphcat.Graph.clear_tasks instead.", DeprecationWarning, stacklevel=2)
        self._require_task_present(name)
        self.clear_tasks(name)


    def set_input(self, source, target, input):
        """.. deprecated:: 0.3.0

            Use :meth:`set_links` instead.
        """
        warnings.warn("graphcat.Graph.set_input is deprecated, use graphcat.Graph.set_links instead.", DeprecationWarning, stacklevel=2)
        self._require_task_present(source)
        self._require_task_present(target)
        self._require_link_present(source, target)
        self._graph.edges[(target, source)]["input"] = input
        self.mark_unfinished(target)


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


    def set_task_fn(self, name, fn):
        """.. deprecated:: 0.3.0

            Use :meth:`set_task` instead.
        """
        warnings.warn("graphcat.Graph.set_task_fn is deprecated, use graphcat.Graph.set_task instead.", DeprecationWarning, stacklevel=2)
        self._require_task_present(name)
        if fn is None:
            fn = null
        self.set_task(name, fn)


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
        """

        self._require_task_present(name)

        # Keep track of failures.
        failed = None

        # Iterate over every task to be executed, in order ...
        for name in networkx.dfs_postorder_nodes(self._graph, name):
            task = self._graph.nodes[name]

            # Notify observers that the task will be updated.
            self._on_update.send(self, name=name)

            # Only execute this task if it isn't finished and a failure hasn't already occurred.
            if failed is None and task["state"] != TaskState.FINISHED:

                try:
                    # Gather inputs for the function.
                    inputs = {}
                    for edge in self._graph.out_edges(name):
                        output = self._graph.nodes[edge[1]]["output"]
                        edge_input = self._graph.edges[edge]["input"]
                        if edge_input not in inputs:
                            inputs[edge_input] = []
                        inputs[edge_input].append(output)

                    # Execute the function and store the output.
                    self._on_execute.send(self, name=name, inputs=inputs)
                    task["output"] = task["fn"](name=name, inputs=inputs)
                    task["state"] = TaskState.FINISHED
                    self._on_finished.send(self, name=name, output=task["output"])
                except Exception as e:
                    # The function raised an exception, notify observers.
                    failed = name
                    task["output"] = None
                    task["state"] = TaskState.FAILED
                    self._on_failed.send(self, name=name, exception=e)

        # If a failure occurred, mark all downstream tasks.
        if failed is not None:
            self.mark_failed(failed)


class Input(enum.Enum):
    """Enumerates special :class:`Graph` named inputs."""
    DEPENDENCY = 1
    """Named input for links that are used only as dependencies, not data sources."""


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

        graph.on_failed.connect(self.on_failed)
        graph.on_execute.connect(self.on_execute)
        graph.on_finished.connect(self.on_finished)
        graph.on_update.connect(self.on_update)

    def on_failed(self, sender, name, exception):
        """Called when a task raises an exception during execution."""
        if self._log_exceptions:
            self._log.error(f"Task {name} failed. Exception: {exception}")
        else:
            self._log.error(f"Task {name} failed.")

    def on_execute(self, sender, name, inputs):
        """Called when a task is executed."""
        if self._log_inputs:
            self._log.info(f"Task {name} executing. Inputs: {inputs}")
        else:
            self._log.info(f"Task {name} executing.")

    def on_finished(self, sender, name, output):
        """Called when a task has executed sucessfully."""
        if self._log_outputs:
            self._log.info(f"Task {name} finished. Output: {output}")
        else:
            self._log.info(f"Task {name} finished.")

    def on_update(self, sender, name):
        """Called when a task is updated."""
        self._log.debug(f"Task {name} updating.")


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

    def _on_update(self, sender, name):
        self._tasks.add(name)

    @property
    def tasks(self):
        """Graph tasks that have received updates since this object was created.

        Returns
        -------
        tasks: set
            Python set containing the names for every task that has been updated.
        """
        return self._tasks



class VariableTask(object):
    """Manage a task that acts as a variable.

    Use :class:`Variable` to create a task that
    will return a given value::

        var = graphcat.Variable(graph, name="theta", value=math.pi)

    when the value needs to change (from user input, for example),
    just use the :meth:`set` method::

        var.set(math.pi / 2)

    ... which will automatically cause downstream tasks that depend on the
    variable to execute the next time they're updated.

    Parameters
    ----------
    graph: :class:`Graph`, required
        The graph that will contain the variable task.
    name: hashable value, required
        The name for the variable task.
    value: Any value, required
        Initial value of the variable.
    """
    def __init__(self, graph, name, value):
        self._graph = graph
        self._name = name
        self._graph.add_task(name, constant(value))

    def set(self, value):
        """Change the underlying task value.

        This will cause downstream tasks to execute the next time they're
        updated.

        Parameters
        ----------
        value: Any value, required
            New value of the variable.
        """
        self._graph.set_task(self._name, constant(value))


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
    def implementation(name, inputs):
        return value
    return implementation


def execute(code, locals={}):
    """Factory for task functions that execute Python expressions.

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
    def implementation(name, inputs):
        return eval(code, {}, dict(locals))
    return implementation


def null(name, inputs):
    """Task function that does nothing.

    This is the default if you don't specify a function for
    :meth:`Graph.add_task` or :meth:`Graph.set_task_fn`, and is useful in
    debugging and pedagogy.
    """
    pass


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
    def implementation(name, inputs):
        raise exception
    return implementation


