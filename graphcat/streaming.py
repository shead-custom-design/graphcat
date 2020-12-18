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

"""Implements computational graphs using dynamic dependency analysis and streaming.
"""

import functools

import graphcat.common
import graphcat.graph


class StreamingGraph(graphcat.graph.Graph):
    """Manages a dynamic streaming computational graph.

    The graph is a collection of named tasks, connected by links that define
    dependencies between tasks.  Updating a task implicitly updates all of its
    transitive dependencies.  When an unfinished task is updated, it executes a
    user-supplied function and stores the function return value as the task
    output.  Outputs of upstream tasks are automatically passed as inputs to
    downstream tasks.
    """
    def __init__(self):
        super().__init__()


    def _add_node(self, name, fn):
        self._graph.add_node(name, fn=fn, state=graphcat.common.TaskState.UNFINISHED, extent=None, output=None, updating=False)


    def _mark_unfinished(self, name):
        node = self._graph.nodes[name]
        node["extent"] = None
        node["output"] = None
        node["state"] = graphcat.common.TaskState.UNFINISHED


    def _output(self, name, extent=None):
        self._update(name, extent)
        return self._graph.nodes[name]["output"]


    def _update(self, name, extent=None):
        # Break cycles
        task = self._graph.nodes[name]
        if task["updating"]:
            self._on_cycle.send(self, name=name)
            return
        task["updating"] = True

        # Notify observers that the task will be updated.
        self._on_update.send(self, name=name)

        # Only execute this task if it isn't already finished.
        if (task["extent"] != extent) or (task["state"] != graphcat.common.TaskState.FINISHED):
            try:
                # Get the task inputs.
                inputs = NamedInputs(self, name)

                # Execute the function and store the output.
                self._on_execute.send(self, name=name, inputs=inputs, extent=extent)
                task["extent"] = extent
                task["output"] = task["fn"](graph=self, name=name, inputs=inputs, extent=extent)
                task["state"] = graphcat.common.TaskState.FINISHED
                self._on_finished.send(self, name=name, output=task["output"])
            except Exception as e:
                # The function raised an exception, notify observers.
                task["extent"] = None
                task["output"] = None
                task["state"] = graphcat.common.TaskState.FAILED
                self._on_failed.send(self, name=name, exception=e)
                task["updating"] = False
                raise e

        task["updating"] = False


    @property
    def is_dynamic(self):
        """Returns :any:`True`."""
        return True


    @property
    def is_streaming(self):
        """Returns :any:`True`."""
        return True


    def output(self, name, extent=None):
        """Retrieve the output from a task.

        This implicitly updates the graph, so the returned value is
        guaranteed to be up-to-date.

        Parameters
        ----------
        name: hashable object, required
            Unique task name.
        extent: hashable object, optional
            Domain object specifying the subset of the task's output to return.

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
        self.update(name, extent)
        return self._graph.nodes[name]["output"]


    def update(self, name, extent=None):
        """Update a task and all of its transitive dependencies.

        Parameters
        ----------
        name: hashable object, required
            Name identifying the task to be updated.
        extent: hashable object, optional
            Domain object specifying the subset of the task's output to compute.

        Raises
        ------
        :class:`ValueError`
            If the task with `name` doesn't exist.
        :class:`Exception`
            Any exception raised by a task function will be re-raised by :meth:`update`.
        """

        self._require_task_present(name)
        self._update(name, extent)


class NamedInputs(object):
    """Access named inputs for a graph task.

    Parameters
    ----------
    graph: :class:`StreamingGraph`, required
        Graph containing a task.
    name: hashable object, required
        Existing task unique name.
    """
    def __init__(self, graph, name):
        if not isinstance(graph, StreamingGraph):
            raise ValueError("Graph input must be an instance of StreamingGraph") # pragma: no cover

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

    def get(self, name, extent=None, default=None):
        """Return a single input value.

        Use this method to return a value when you expect to have either zero
        or one input that matches `name`.

        Parameters
        ----------
        name: hashable object, required
            Name of the input value to return.
        extent: hashable object, optional
            Domain object specifying the subset of the input's value to return.
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
            return values[0](extent)
        else:
            raise KeyError(f"More than one input {name!r}")

    def getall(self, name, extent=None):
        """Return multiple input values.

        Use this method to return every input value that matches `name`.

        Parameters
        ----------
        name: hashable object, required
            Name of the input value to return.
        extent: hashable object, optional
            Domain object specifying the subset of each input's value to return.

        Returns
        -------
        values: list of Python values
            Values from every input that matches `name`.  Returns an empty list
            if there are none.
        """
        return [value(extent) for key, value in zip(self._keys, self._values) if key == name]

    def getone(self, name, extent=None):
        """Return a single input value.

        Use this method to return a value when you expect to have exactly one
        input that matches `name`.

        Parameters
        ----------
        name: hashable object, required
            Name of the input value to return.
        extent: hashable object, optional
            Domain object specifying the subset of each input's value to return.

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
            return values[0](extent)
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


