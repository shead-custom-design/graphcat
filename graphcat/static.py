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

"""Implements computational graphs using static dependency analysis.
"""

import collections
import warnings

import blinker
import networkx

import graphcat.common

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
            self._graph.nodes[name]["state"] = graphcat.common.TaskState.FAILED

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
            self._graph.add_node(name, fn=fn, state=graphcat.common.TaskState.UNFINISHED, output=None)
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
            if exception is None and task["state"] != graphcat.common.TaskState.FINISHED:

                try:
                    # Gather inputs for the function.
                    inputs = NamedInputs(self, name)

#                    inputs = collections.defaultdict(list)
#                    for target, source, input in self._graph.out_edges(name, data="input"):
#                        output = self._graph.nodes[source]["output"]
#                        inputs[input].append(output)
#                    inputs = dict(inputs)

                    # Execute the function and store the output.
                    self._on_execute.send(self, name=name, inputs=inputs)
                    task["output"] = task["fn"](graph=self, name=name, inputs=inputs)
                    task["state"] = graphcat.common.TaskState.FINISHED
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


class NamedInputs(object):
    def __init__(self, graph, name):
        def constant(value):
            def implementation():
                return value
            return implementation

        edges = graph._graph.out_edges(name, data="input")
        self._keys = [input for target, source, input in edges]
        self._values = [constant(graph._graph.nodes[source]["output"]) for target, source, input in edges]

    def __contains__(self, name):
        return name in self._keys

    def __getitem__(self, key):
        """.. deprecated:: 0.10.0"""
        warnings.warn("NamedInputs.__getitem__() is deprecated, use NamedInputs.get(), NamedInputs.getone(), or NamedInputs.getall() instead.", DeprecationWarning, stacklevel=2)
        return self.getall(key)

    def __len__(self):
        return len(self._keys)

    def __repr__(self):
        inputs = ", ".join([f"{key}: {value()}" for key, value in zip(self._keys, self._values)])
        return f"{{{inputs}}}"

    def get(self, name, default=None):
        values = [value for key, value in zip(self._keys, self._values) if key == name]
        if len(values) == 0:
            return default
        elif len(values) == 1:
            return values[0]()
        else:
            raise KeyError(f"More than one input {name!r}")

    def getall(self, name):
        return [value() for key, value in zip(self._keys, self._values) if key == name]

    def getone(self, name):
        values = [value for key, value in zip(self._keys, self._values) if key == name]
        if len(values) == 0:
            raise KeyError(name)
        elif len(values) == 1:
            return values[0]()
        else:
            raise KeyError(f"More than one input {name!r}")

    def items(self):
        return zip(self._keys, self._values)

    def keys(self):
        return self._keys

    def values(self):
        return self._values

