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

import sys
import unittest.mock

from behave import *

import graphcat
import graphcat.diagram
import graphcat.notebook

try:
    import pygraphviz
except:
    pass

try:
    import IPython
except:
    pass

try:
    import numpy
    import numpy.testing
except:
    pass

import test


class EventRecorder(object):
    def __init__(self, graph):
        self.changed = []
        self.cycles = []
        self.exceptions = []
        self.executed = []
        self.failed = []
        self.finished = []
        self.inputs = []
        self.outputs = []
        self.task_renamed = []
        self.updated = []

        graph.on_changed.connect(self.on_changed)
        graph.on_cycle.connect(self.on_cycle)
        graph.on_execute.connect(self.on_execute)
        graph.on_failed.connect(self.on_failed)
        graph.on_finished.connect(self.on_finished)
        graph.on_task_renamed.connect(self.on_task_renamed)
        graph.on_update.connect(self.on_update)

    def on_changed(self, graph):
        self.changed.append(graph)

    def on_cycle(self, graph, name):
        self.cycles.append(name)

    def on_execute(self, graph, name, inputs, extent=None):
        self.executed.append(name)
        self.inputs.append(inputs)

    def on_failed(self, graph, name, exception):
        self.failed.append(name)
        self.exceptions.append(exception)

    def on_finished(self, graph, name, output):
        self.finished.append(name)
        self.outputs.append(output)

    def on_task_renamed(self, graph, oldname, newname):
        self.task_renamed.append((oldname, newname))

    def on_update(self, graph, name, extent=None):
        self.updated.append(name)


#################################################################
# Givens

@given(u'the {module} module is available')
def step_impl(context, module):
    if module not in sys.modules:
        context.scenario.skip()


@given(u'an empty dynamic graph')
def step_impl(context):
    context.graph = graphcat.DynamicGraph()


@given(u'an empty static graph')
def step_impl(context):
    context.graph = graphcat.StaticGraph()


@given(u'an empty streaming graph')
def step_impl(context):
    context.graph = graphcat.StreamingGraph()


@given(u'a log')
def step_impl(context):
    context.log = unittest.mock.Mock()


@given(u'a graph logger')
def step_impl(context):
    context.logger = graphcat.Logger(context.graph, log=context.log)


@given(u'a graph logger with detailed outputs disabled')
def step_impl(context):
    context.logger = graphcat.Logger(context.graph, log_exceptions=False, log_inputs=False, log_outputs=False, log_extents=False, log=context.log)


@given(u'a performance monitor')
def step_impl(context):
    context.performance_monitor = graphcat.PerformanceMonitor(context.graph)


#################################################################
# Whens


@when(u'adding an expression task {name} with expression {expression}')
def step_impl(context, name, expression):
    name = eval(name)
    expression = eval(expression)
    context.events = EventRecorder(context.graph)
    context.graph.set_expression(name, expression)


@when(u'changing the expression task {name} to expression {expression}')
def step_impl(context, name, expression):
    name = eval(name)
    expression = eval(expression)
    context.events = EventRecorder(context.graph)
    context.graph.set_expression(name, expression)


@when(u'adding tasks {names} with functions {functions}')
def step_impl(context, names, functions):
    names = eval(names)
    functions = eval(functions)
    context.events = EventRecorder(context.graph)
    for name, function in zip(names, functions):
        context.graph.add_task(name, function)


@when(u'adding task {name} an exception should be raised')
def step_impl(context, name):
    name = eval(name)
    context.events = EventRecorder(context.graph)
    with test.assert_raises(ValueError):
        context.graph.add_task(name)


@when(u'adding link {link} an exception should be raised')
def step_impl(context, link):
    source, target = eval(link)
    context.events = EventRecorder(context.graph)
    with test.assert_raises(ValueError):
        context.graph.add_links(source, target)


@when(u'adding links {links}')
def step_impl(context, links):
    links = eval(links)
    context.events = EventRecorder(context.graph)
    for source, targets in links:
        context.graph.add_links(source, targets)


@when(u'setting links {links}')
def step_impl(context, links):
    links = eval(links)
    context.events = EventRecorder(context.graph)
    for source, targets in links:
        context.graph.set_links(source, targets)


@when(u'setting parameter {target} {input} {source} {value}')
def step_impl(context, source, value, target, input):
    source = eval(source)
    value = eval(value)
    target = eval(target)
    input = eval(input)
    context.events = EventRecorder(context.graph)
    context.graph.set_parameter(target, input, source, value)


@when(u'adding tasks {names}')
def step_impl(context, names):
    names = eval(names)
    context.events = EventRecorder(context.graph)
    for name in names:
        context.graph.add_task(name)


@when(u'updating task {name} with extent {extent} an exception should be raised')
def step_impl(context, name, extent):
    name = eval(name)
    extent = eval(extent)
    context.events = EventRecorder(context.graph)
    with test.assert_raises(RuntimeError):
        context.graph.update(name, extent=extent)


@when(u'updating task {name} an exception should be raised')
def step_impl(context, name):
    name = eval(name)
    context.events = EventRecorder(context.graph)
    with test.assert_raises(RuntimeError):
        context.graph.update(name)


@when(u'renaming tasks {oldnames} as {newnames}')
def step_impl(context, oldnames, newnames):
    oldnames = eval(oldnames)
    newnames = eval(newnames)
    context.events = EventRecorder(context.graph)
    for oldname, newname in zip(oldnames, newnames):
        context.graph.rename_task(oldname, newname)


@when(u'removing link {link} no exception should be raised')
def step_impl(context, link):
    source, target = eval(link)
    context.events = EventRecorder(context.graph)
    context.graph.clear_links(source, target)


@when(u'removing links {links}')
def step_impl(context, links):
    links = eval(links)
    context.events = EventRecorder(context.graph)
    for source, target in links:
        context.graph.clear_links(source, target)


@when(u'updating tasks {names} with extents {extents}')
def step_impl(context, names, extents):
    names = eval(names)
    extents = eval(extents)
    context.events = EventRecorder(context.graph)
    for name, extent in zip(names, extents):
        context.graph.update(name, extent=extent)


@when(u'updating tasks {names}')
def step_impl(context, names):
    names = eval(names)
    context.events = EventRecorder(context.graph)
    for name in names:
        context.graph.update(name)


@when(u'removing tasks {names} with clear_tasks')
def step_impl(context, names):
    names = eval(names)
    context.events = EventRecorder(context.graph)
    context.graph.clear_tasks(names)


@when(u'the task {name} function is changed to {function}')
def step_impl(context, name, function):
    name = eval(name)
    function = eval(function)
    context.events = EventRecorder(context.graph)
    context.graph.set_task(name, function)


@when(u'tasks {names} are marked unfinished')
def step_impl(context, names):
    names = eval(names)
    for name in names:
        context.graph.mark_unfinished(name)


@when(u'the performance monitor is reset')
def step_impl(context):
    context.performance_monitor.reset()


@when(u'filtering the graph with {hide} then the remaining nodes should match {names}')
def step_impl(context, hide, names):
    hide = eval(hide)
    names = eval(names)

    remaining = [name for name in context.graph.tasks() if not hide(context.graph, name)]
    test.assert_equal(sorted(remaining), sorted(names))


@when(u'computing the task {names} outputs with extents {extents}')
def step_impl(context, names, extents):
    names = eval(names)
    extents = eval(extents)
    context.events = EventRecorder(context.graph)
    context.outputs = [context.graph.output(name, extent=extent) for name, extent in zip(names, extents)]


@when(u'computing the task {names} outputs')
def step_impl(context, names):
    names = eval(names)
    context.events = EventRecorder(context.graph)
    context.outputs = [context.graph.output(name) for name in names]


@when(u'the graph is converted to a diagram')
def step_impl(context):
    context.agraph = graphcat.diagram.draw(context.graph)


#################################################################
# Thens

@then(u'the graph should contain tasks {names}')
def step_impl(context, names):
    names = eval(names)
    test.assert_equal(context.graph.tasks(), set(names))


@then(u'the graph should contain links {links}')
def step_impl(context, links):
    links = eval(links)
    test.assert_equal(sorted(links), sorted(context.graph.links()))


@then(u'the outputs should be {outputs}')
def step_impl(context, outputs):
    outputs = eval(outputs)
    test.assert_equal(outputs, context.outputs)


@then(u'the numpy outputs should be {outputs}')
def step_impl(context, outputs):
    outputs = eval(outputs)
    for a, b in zip(outputs, context.outputs):
        numpy.testing.assert_allclose(a, b)


@then(u'the task {names} state is failed')
def step_impl(context, names):
    names = eval(names)
    for name in names:
        test.assert_equal(context.graph.state(name), graphcat.TaskState.FAILED)


@then(u'the task {names} state is finished')
def step_impl(context, names):
    names = eval(names)
    for name in names:
        test.assert_equal(context.graph.state(name), graphcat.TaskState.FINISHED)


@then(u'the task {names} state is unfinished')
def step_impl(context, names):
    names = eval(names)
    for name in names:
        test.assert_equal(context.graph.state(name), graphcat.TaskState.UNFINISHED)


@then(u'tasks {oldnames} should be renamed to {newnames}')
def step_impl(context, oldnames, newnames):
    oldnames = eval(oldnames)
    newnames = eval(newnames)
    test.assert_equal(list(zip(oldnames, newnames)), context.events.task_renamed)


@then(u'tasks {names} are updated')
def step_impl(context, names):
    names = eval(names)
    test.assert_equal(names, context.events.updated)


@then(u'task {name} has {count} inputs')
def step_impl(context, name, count):
    name = eval(name)
    count = eval(count)
    index = context.events.executed.index(name)
    inputs = context.events.inputs[index]
    test.assert_equal(count, len(inputs))


@then(u'the task {name} inputs contain {key}')
def step_impl(context, name, key):
    name = eval(name)
    key = eval(key)
    index = context.events.executed.index(name)
    inputs = context.events.inputs[index]
    test.assert_true(key in inputs)


@then(u'the task {name} inputs do not contain {key}')
def step_impl(context, name, key):
    name = eval(name)
    key = eval(key)
    index = context.events.executed.index(name)
    inputs = context.events.inputs[index]
    test.assert_true(key not in inputs)


@then(u'getting input {key} from task {name} returns {value}')
def step_impl(context, key, name, value):
    key = eval(key)
    name = eval(name)
    value = eval(value)
    index = context.events.executed.index(name)
    inputs = context.events.inputs[index]
    test.assert_equal(inputs.get(key), value)


@then(u'getting input {key} from task {name} raises {exception}')
def step_impl(context, key, name, exception):
    key = eval(key)
    name = eval(name)
    exception = eval(exception)
    index = context.events.executed.index(name)
    inputs = context.events.inputs[index]
    with test.assert_raises(exception):
        inputs.get(key)


@then(u'getting one input from task {name} input {key} returns {value}')
def step_impl(context, key, name, value):
    key = eval(key)
    name = eval(name)
    value = eval(value)
    index = context.events.executed.index(name)
    inputs = context.events.inputs[index]
    test.assert_equal(inputs.getone(key), value)


@then(u'getting one input from task {name} input {key} raises {exception}')
def step_impl(context, key, name, exception):
    key = eval(key)
    name = eval(name)
    exception = eval(exception)
    index = context.events.executed.index(name)
    inputs = context.events.inputs[index]
    with test.assert_raises(exception):
        inputs.getone(key)


@then(u'getting all inputs from task {name} input {key} returns {values}')
def step_impl(context, name, key, values):
    key = eval(key)
    name = eval(name)
    values = eval(values)
    index = context.events.executed.index(name)
    inputs = context.events.inputs[index]
    test.assert_equal(values, inputs.getall(key))


@then(u'getting the task {name} input keys returns {values}')
def step_impl(context, name, values):
    name = eval(name)
    values = eval(values)
    index = context.events.executed.index(name)
    inputs = context.events.inputs[index]
    test.assert_equal(values, list(inputs.keys()))


@then(u'getting the task {name} input values returns {values}')
def step_impl(context, name, values):
    name = eval(name)
    values = eval(values)
    index = context.events.executed.index(name)
    inputs = context.events.inputs[index]
    test.assert_equal(values, [value() for value in inputs.values()])


@then(u'getting the task {name} input items returns {values}')
def step_impl(context, name, values):
    name = eval(name)
    values = eval(values)
    index = context.events.executed.index(name)
    inputs = context.events.inputs[index]
    test.assert_equal(values, [(key, value()) for key, value in inputs.items()])


@then(u'tasks {names} detect cycles')
def step_impl(context, names):
    names = eval(names)
    test.assert_equal(names, context.events.cycles)


@then(u'tasks {names} are executed')
def step_impl(context, names):
    names = eval(names)
    test.assert_equal(names, context.events.executed)


@then(u'tasks {names} are finished')
def step_impl(context, names):
    names = eval(names)
    test.assert_equal(names, context.events.finished)


@then(u'the log should contain {calls}')
def step_impl(context, calls):
    calls = eval(calls)

    calls = [(call[0], (call[1],), {}) for call in calls]
    mock_calls = [tuple(call) for call in context.logger._log.mock_calls]
    test.assert_equal(calls, mock_calls)
    context.logger._log.reset_mock()


@then(u'the graph can be drawn as a diagram')
def step_impl(context):
    agraph = graphcat.diagram.draw(context.graph)


@then(u'displaying the graph in a notebook should produce a visualization')
def step_impl(context):
    graphcat.notebook.display(context.graph)


@then(u'the diagram can be displayed in a notebook')
def step_impl(context):
    graphcat.notebook.display(context.agraph)


@then(u'the graph can be drawn as a diagram with performance overlay')
def step_impl(context):
    agraph = graphcat.diagram.draw(context.graph)
    agraph = graphcat.diagram.performance(agraph, context.performance_monitor)


@then(u'tasks {names} should have links {links}')
def step_impl(context, names, links):
    names = eval(names)
    links = eval(links)
    test.assert_equal(sorted(links), sorted(context.graph.links(names)))


@then(u'testing if the graph contains task {task} should return {result}')
def step_impl(context, task, result):
    task = eval(task)
    result = eval(result)
    test.assert_equal(task in context.graph, result)


@then(u'the performance monitor output should be {outputs}')
def step_impl(context, outputs):
    outputs = eval(outputs)

    monitor = context.performance_monitor
    test.assert_dict_list_values_close(outputs, monitor.tasks, places=None, delta=0.01)


