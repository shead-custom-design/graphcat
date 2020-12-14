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

"""Implements computational graphs using dynamic dependency analysis.
"""

import collections
import functools

import blinker
import networkx

import graphcat.common

class DynamicGraph(object):
    """Manages a dynamic computational graph.

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
        self._on_cycle = blinker.Signal()
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
            If :any:`None` (the default), :func:`graphcat.common.null` will be used.

        Raises
        ------
        :class:`ValueError`
            If `label` already exists.
        """
        self._require_task_absent(name)
        if fn is None:
            fn = graphcat.common.null
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
            self._graph.nodes[name]["state"] = graphcat.common.TaskState.UNFINISHED

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
    def on_cycle(self):
        """Signal emitted if a cycle is detected during updating.

        Functions invoked by this signal must have the signature fn(graph, name),
        where `graph` is this object.

        Returns
        -------
        signal: :class:`blinker.base.Signal`
        """
        return self._on_cycle


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
        fn = graphcat.common.execute(expression, locals)
        fn = graphcat.common.automatic_dependencies(fn)
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
        self.set_task(source, graphcat.common.constant(value))
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
            self._graph.add_node(name, fn=fn, state=graphcat.common.TaskState.UNFINISHED, output=None, updating=False)
        self.mark_unfinished(name)


    def state(self, name):
        """Return the current state of a task.

        Parameters
        ----------
        name: hashable object, required
            Unique name that identifies the task.

        Returns
        -------
        state: :class:`graphcat.common.TaskState`
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


    def _output(self, name):
        self._update(name)
        return self._graph.nodes[name]["output"]


    def _update(self, name):
        # Break cycles
        task = self._graph.nodes[name]
        if task["updating"]:
            self._on_cycle.send(self, name=name)
            return
        task["updating"] = True

        # Notify observers that the task will be updated.
        self._on_update.send(self, name=name)

        # Only execute this task if it isn't already finished.
        if task["state"] != graphcat.common.TaskState.FINISHED:
            try:
                # Get the task inputs.
                inputs = NamedInputs(self, name)

                # Execute the function and store the output.
                self._on_execute.send(self, name=name, inputs=inputs)
                task["output"] = task["fn"](graph=self, name=name, inputs=inputs)
                task["state"] = graphcat.common.TaskState.FINISHED
                self._on_finished.send(self, name=name, output=task["output"])
            except Exception as e:
                # The function raised an exception, notify observers.
                task["output"] = None
                task["state"] = graphcat.common.TaskState.FAILED
                self._on_failed.send(self, name=name, exception=e)
                task["updating"] = False
                raise e

        task["updating"] = False


    def update(self, name):
        """Update a task and all of its transitive dependencies.

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
        self._update(name)


class NamedInputs(object):
    """Access named inputs for a graph task.

    Parameters
    ----------
    graph: :class:`DynamicGraph`, required
        Graph containing a task.
    name: hashable object, required
        Existing task unique name.
    """
    def __init__(self, graph, name):
        if not isinstance(graph, DynamicGraph):
            raise ValueError("Graph input must be an instance of DynamicGraph") # pragma: no cover

        edges = graph._graph.out_edges(name, data="input")
        self._keys = [input for target, source, input in edges]
        self._values = [functools.partial(graph._output, source) for target, source, input in edges]

    def __contains__(self, name):
        """Return :any:`True` if `name` matches a named input for this task."""
        return name in self._keys

    def __len__(self):
        """Return the number of named inputs for this task."""
        return len(self._keys)

    def __repr__(self):
        inputs = ", ".join([repr(key) for key in self._keys])
        return f"{{{inputs}}}"

    def get(self, name, default=None):
        """Return a single input value.

        Use this method to return a value when you expect to have either zero
        or one input that matches `name`.

        Parameters
        ----------
        name: hashable object, required
            Name of the input value to return.
        default: any Python value, optional
            If an input matching `name` doesn't exist, this value will be
            returned instead.  Defaults to :any:`None`.

        Returns
        -------
        value: any Python value
            The value of input `name`, or `default`.

        Raises
        ------
        :class:`KeyError`: if more than one input matches `name`.
        """
        values = [value for key, value in zip(self._keys, self._values) if key == name]
        if len(values) == 0:
            return default
        elif len(values) == 1:
            return values[0]()
        else:
            raise KeyError(f"More than one input {name!r}")

    def getall(self, name):
        """Return multiple input values.

        Use this method to return every input value that matches `name`.

        Parameters
        ----------
        name: hashable object, required
            Name of the input value to return.

        Returns
        -------
        values: list of Python values
            Values from every input that matches `name`.  Returns an empty list
            if there are none.
        """
        return [value() for key, value in zip(self._keys, self._values) if key == name]

    def getone(self, name):
        """Return a single input value.

        Use this method to return a value when you expect to have exactly one
        input that matches `name`.

        Parameters
        ----------
        name: hashable object, required
            Name of the input value to return.

        Returns
        -------
        value: any Python value
            The value of input `name`.

        Raises
        ------
        :class:`KeyError`: if more or less than one input matches `name`.
        """
        values = [value for key, value in zip(self._keys, self._values) if key == name]
        if len(values) == 0:
            raise KeyError(name)
        elif len(values) == 1:
            return values[0]()
        else:
            raise KeyError(f"More than one input {name!r}")

    def items(self):
        """Return names and values for every input attached to this task.

        Note
        ----
        For each (name, value) pair returned by this method, the value is a
        callable that returns the actual value from the upstream task.

        Returns
        -------
        values: sequence of (hashable object, callable) tuples
            The name and value of every input attached to this task.
        """
        return zip(self._keys, self._values)

    def keys(self):
        """Return names for every input attached to this task.

        Returns
        -------
        names: sequence of hashable objects
            The name of every input attached to this task.  Note that the same
            name may appear more than once in the sequence.
        """
        return self._keys

    def values(self):
        """Return values for every input attached to this task.

        Note
        ----
        Each value returned by this method is a callable that returns the
        actual value from the upstream task.

        Returns
        -------
        values: sequence of callables
            The value of every input attached to this task, in the same
            order as :meth:`keys`.
        """
        return self._values


