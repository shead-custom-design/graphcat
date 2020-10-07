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

__version__ = "0.1.0"

import enum
import functools
import logging

import blinker
import networkx

log = logging.getLogger(__name__)


class ExpressionTask(object):
    """Manage a task that executes Python expressions and tracks implicit dependencies.

    Parameters
    ----------
    graph: class:`Graph`, required
        The graph where the new expression task will be created.
    label: hashable object, required
        Unique label for the new expression task.
    expression: string, required
        Python expression that will be executed whenever the task is executed.
    locals: dict, optional
        Optional dictionary containing local objects that will be available for
        use in the expression.
    """
    def __init__(self, graph, label, expression, locals={}):
        self._graph = graph
        self._label = label

        self._graph.add_task(label)
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
        self._graph.set_task_fn(self._label, execute(expression, locals))

        sources = list(self._graph._graph.successors(self._label))
        for source in sources:
            self._graph._graph.remove_edge(self._label, source)

        updated = UpdatedTasks(self._graph)
        self._graph.update(self._label)

        sources = updated.tasks.difference([self._label])
        for source in sources:
            self._graph._graph.add_edge(self._label, source, input=Input.DEPENDENCY)


class Graph(object):
    """Manages a computational graph.

    The graph is a collection of labelled tasks, connected by relationships that define
    dependencies between tasks.  Updating a task implicitly updates all of its
    transitive dependencies.  When a task is updated, it executes a
    user-supplied function and stores the function return value as thetask 
    output.  Outputs of upstream tasks are automatically passed as inputs to
    downstream tasks.
    """
    def __init__(self):
        self._graph = networkx.DiGraph()
        self._on_failed = blinker.Signal()
        self._on_execute = blinker.Signal()
        self._on_finished = blinker.Signal()
        self._on_update = blinker.Signal()

    def _require_task_present(self, label):
        if label not in self._graph:
            raise ValueError(f"Task {label} doesn't exist.")

    def _require_task_absent(self, label):
        if label in self._graph:
            raise ValueError(f"Task {label} already exists.")

    def _require_relationship_present(self, source, target):
        if self._graph.number_of_edges(target, source) != 1:
            raise ValueError(f"Edge {source} -> {target} doesn't exist.")

    def add_relationship(self, source, target, input=None):
        """Make source a dependency of target.

        To indicate that `target` depends on (is a consumer of data from)
        `source` use :meth:`add_relationship`::

            graph.add_relationship("png_reader", "blur")

        For tasks that require multiple inputs, assign unique values to `input` so that they
        can distinguish among them::

            graph.add_relationship("png_reader", "blur", input="image")
            graph.add_relationship("blur_radius", "blur", input="radius")

        Parameters
        ----------
        source: hashable object, required
            Label identifying the task that will act as a data source.
        target: hashable object, required
            Label identifying the task that will act as a data consumer.
        input: hashable object, optional
            Identifies which `target` input this relationship will feed.  Left unspecified, this will default to :class:`Input.DEFAULT`.

        Raises
        ------
        :class:`ValueError`
            If `source` or `target` don't exist.
        """
        self._require_task_present(source)
        self._require_task_present(target)
        if input is None:
            input = Input.DEFAULT
        self._graph.add_edge(target, source, input=input) # Edges point from tasks to their dependencies.
        self.mark_unfinished(target)

    def add_task(self, label, fn=None):
        """Add a task to the graph.

        Parameters
        ----------
        label: hashable object, required
            Unique label that will identify the task.
        fn: callable, optional
            The `fn` object will be called whenever the task is executed.  It must take two keyword arguments
            as parameters, `label` and `inputs`.  `label` will contain the unique task label.  `inputs` will
            be a dict mapping each relationship's named `input` to a sequence of outputs returned from this task's dependencies
            (upstream tasks).  If `None` (the default), :func:`null` will be used.

        Raises
        ------
        :class:`ValueError`
            If `label` already exists.
        """
        self._require_task_absent(label)
        if fn is None:
            fn = null
        self._graph.add_node(label, fn=fn, state=TaskState.UNFINISHED, updating=False, output=None)


    def state(self, label):
        """Return the current state of a task.

        Parameters
        ----------
        label: hashable object, required
            Unique label that identifies the task.

        Returns
        -------
        state: :class:`TaskState`
            Enumeration describing the current task state.

        Raises
        ------
        :class:`ValueError`
            If `label` doesn't exist.
        """
        self._require_task_present(label)
        return self._graph.nodes[label]["state"]


    def mark_failed(self, label):
        """Set the failed state for a task and all downstream dependents.

        Normally, the failed state is set automatically by :meth:`update`.  This
        method is provided for callers who want to set the failed state in
        response to some outside event that the graph isn't aware of; this
        should only happen in extremely rare situations.

        Parameters
        ----------
        label: hashable object, required
            Unique task label.

        Raises
        ------
        :class:`ValueError`
            If `label` doesn't exist.
        """
        self._require_task_present(label)
        labels = networkx.ancestors(self._graph, label)
        labels.add(label)
        for label in labels:
            self._graph.nodes[label]["output"] = None
            self._graph.nodes[label]["state"] = TaskState.FAILED

    def mark_unfinished(self, label):
        """Set the unfinished state for a task and all downstream dependents.

        Callers should use :meth:`mark_unfinished` to indicate that a task has
        changed.  Ideally, this should rarely be necessary.

        Parameters
        ----------
        label: hashable object, required
            Unique task label.

        Raises
        ------
        :class:`ValueError`
            If `label` doesn't exist.
        """
        self._require_task_present(label)
        labels = networkx.ancestors(self._graph, label)
        labels.add(label)
        for label in labels:
            self._graph.nodes[label]["output"] = None
            self._graph.nodes[label]["state"] = TaskState.UNFINISHED

    @property
    def on_failed(self):
        """Signal emitted when a task fails during execution.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_failed

    @property
    def on_execute(self):
        """Signal emitted before a task is executed.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_execute

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

    def output(self, label):
        """Retrieve the output from a task.

        This implicitly updates the graph, so the returned value is
        guaranteed to be up-to-date.

        Parameters
        ----------
        label: hashable object, required
            Unique task label.

        Returns
        -------
        output: any object
            The value returned when the task function was last executed, or `None`.

        Raises
        ------
        :class:`ValueError`
            If `label` doesn't exist.
        """
        self._require_task_present(label)
        self.update(label)
        return self._graph.nodes[label]["output"]

    def relabel_task(self, label, newlabel):
        """Change an existing task's label.

        This modifies an existing task's label, and handles modifying relationships
        as-necessary.  In addition, the task and any downstream dependents will
        be marked as out-of-date.

        Parameters
        ----------
        label: hashable object, required
            Unique task label.
        newlabel: hashable object, required
            Unique new task label.

        Raises
        ------
        :class:`ValueError`
            If the task with `label` doesn't exist, or a task with `newlabel` already exists.
        """
        self._require_task_present(label)
        self._require_task_absent(newlabel)
        networkx.relabel_nodes(self._graph, mapping = {label: newlabel}, copy=False)
        self.mark_unfinished(newlabel)

    def remove_relationship(self, source, target):
        """Remove a dependency between source and target.

        After performing this operation, changes to `source` will no longer
        cause changes to `target`.  Note that this will also cause downstream
        tasks to be updated.

        Parameters
        ----------
        source: hashable object, required
            Label identifying the source task.
        target: hashable object, required
            Label identifying the target task.

        Raises
        ------
        :class:`ValueError`
            If `source` or `target` don't exist, or there is no existing relationship between them.
        """
        self._require_task_present(source)
        self._require_task_present(target)
        self._require_relationship_present(source, target)
        self.mark_unfinished(source)
        self._graph.remove_edge(target, source)

    def remove_task(self, label):
        """Remove a task from the graph, and any related dependencies.

        Note that this will mark downstream tasks for update.

        Parameters
        ----------
        label: hashable object, required
            Label identifying the task to remove.

        Raises
        ------
        :class:`ValueError`
            If the task with `label` doesn't exist.
        """
        self._require_task_present(label)
        self.mark_unfinished(label)
        self._graph.remove_node(label)

    def set_task_fn(self, label, fn):
        """Change the function that will be executed whan a task is updated.

        Note that this will mark downstream tasks for update.

        Parameters
        ----------
        label: hashable object, required
            Label identifying the task whose function will be set.
        fn: callable object, optional
            New function to be executed when the task is updated.  If `None`
            (the default), :func:`null` will be used instead.

        Raises
        ------
        :class:`ValueError`
            If the task with `label` doesn't exist.
        """
        self._require_task_present(label)
        if fn is None:
            fn = null
        self._graph.nodes[label]["fn"] = fn
        self.mark_unfinished(label)

    def set_input(self, source, target, input):
        """Change the target input that an existing relationship will feed.

        Note that this will mark downstream tasks for update.

        Parameters
        ----------
        source: hashable object, required
            Label identifying the relationship source.
        target: hashable object, required
            Label identifying the relationship target.
        input: hashable object, optional
            Identifies which `target` input this relationship will feed.

        Raises
        ------
        :class:`ValueError`
            If the relationship connecting `source` and `target` doesn't exist.
        """
        self._require_task_present(source)
        self._require_task_present(target)
        self._require_relationship_present(source, target)
        self._graph.edges[(target, source)]["input"] = input
        self.mark_unfinished(target)

    def update(self, label):
        """Update a task and all its transitive dependencies.

        Parameters
        ----------
        label: hashable object, required
            Label identifying the task to be updated.

        Raises
        ------
        :class:`ValueError`
            If the task with `label` doesn't exist.
        """

        self._require_task_present(label)

        # Keep track of failures.
        failed = None

        # Iterate over every task to be executed, in order ...
        for label in networkx.dfs_postorder_nodes(self._graph, label):
            task = self._graph.nodes[label]

            # Notify observers that the task will be updated.
            self._on_update.send(self, label=label)

            # Only execute this task if it isn't finished and a failure hasn't already occurred.
            if failed is None and task["state"] != TaskState.FINISHED:

                try:
                    # Gather inputs for the function.
                    inputs = {}
                    for edge in self._graph.out_edges(label):
                        output = self._graph.nodes[edge[1]]["output"]
                        edge_input = self._graph.edges[edge]["input"]
                        if edge_input not in inputs:
                            inputs[edge_input] = []
                        inputs[edge_input].append(output)

                    # Execute the function and store the output.
                    self._on_execute.send(self, label=label, inputs=inputs)
                    task["output"] = task["fn"](label=label, inputs=inputs)
                    task["state"] = TaskState.FINISHED
                    self._on_finished.send(self, label=label, output=task["output"])
                except Exception as e:
                    # The function raised an exception, notify observers.
                    failed = label
                    task["output"] = None
                    task["state"] = TaskState.FAILED
                    self._on_failed.send(self, label=label, exception=e)

        # If a failure occurred, mark all downstream tasks.
        if failed is not None:
            self.mark_failed(failed)


class Input(enum.Enum):
    """Enumerates special :class:`Graph` named inputs."""
    DEFAULT = 1
    """Default when the caller doesn't explicitly specify a named input."""
    DEPENDENCY = 2
    """Named input for relationships that are used only as dependencies, not data sources."""


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

    def on_failed(self, sender, label, exception):
        """Called when a task raises an exception during execution."""
        if self._log_exceptions:
            self._log.error(f"Task {label} failed. Exception: {exception}")
        else:
            self._log.error(f"Task {label} failed.")

    def on_execute(self, sender, label, inputs):
        """Called when a task is executed."""
        if self._log_inputs:
            self._log.info(f"Task {label} executing. Inputs: {inputs}")
        else:
            self._log.info(f"Task {label} executing.")

    def on_finished(self, sender, label, output):
        """Called when a task has executed sucessfully."""
        if self._log_outputs:
            self._log.info(f"Task {label} finished. Output: {output}")
        else:
            self._log.info(f"Task {label} finished.")

    def on_update(self, sender, label):
        """Called when a task is updated."""
        self._log.debug(f"Task {label} updating.")


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

    def _on_update(self, sender, label):
        self._tasks.add(label)

    @property
    def tasks(self):
        """Graph tasks that have received updates since this object was created.

        Returns
        -------
        tasks: set
            Python set containing the labels for every task that has been updated.
        """
        return self._tasks



class VariableTask(object):
    """Manage a task that acts as a variable.

    Use :class:`Variable` to create a task that
    will return a given value::

        var = graphcat.Variable(graph, label="theta", value=math.pi)

    when the value needs to change (from user input, for example),
    just use the :meth:`set` method::

        var.set(math.pi / 2)

    ... which will automatically cause downstream tasks that depend on the
    variable to execute the next time they're updated.

    Parameters
    ----------
    graph: :class:`Graph`, required
        The graph that will contain the variable task.
    label: hashable value, required
        The label for the variable task.
    value: Any value, required
        Initial value of the variable.
    """
    def __init__(self, graph, label, value):
        self._graph = graph
        self._label = label
        self._graph.add_task(label, constant(value))

    def set(self, value):
        """Change the underlying task value.

        This will cause downstream tasks to execute the next time they're
        updated.

        Parameters
        ----------
        value: Any value, required
            New value of the variable.
        """
        self._graph.set_task_fn(self._label, constant(value))


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
    def implementation(label, inputs):
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
    def implementation(label, inputs):
        return eval(code, {}, dict(locals))
    return implementation


def null(label, inputs):
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
    def implementation(label, inputs):
        raise exception
    return implementation


