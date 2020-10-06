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

from behave import *

import unittest.mock

import graphcat
import graphcat.notebook

import test


class EventRecorder(object):
    def __init__(self, graph):
        self._exceptions = []
        self._executed = []
        self._failed = []
        self._finished = []
        self._inputs = []
        self._outputs = []
        self._updated = []

        graph.on_execute.connect(self.on_execute)
        graph.on_failed.connect(self.on_failed)
        graph.on_finished.connect(self.on_finished)
        graph.on_update.connect(self.on_update)

    @property
    def exceptions(self):
        return self._exceptions

    @property
    def executed(self):
        return self._executed

    @property
    def failed(self):
        return self._failed

    @property
    def finished(self):
        return self._finished

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        return self._outputs

    @property
    def updated(self):
        return self._updated

    def on_execute(self, sender, label, inputs):
        self._executed.append(label)
        self._inputs.append(inputs)

    def on_failed(self, sender, label, exception):
        self._failed.append(label)
        self._exceptions.append(exception)

    def on_finished(self, sender, label, output):
        self._finished.append(label)
        self._outputs.append(output)

    def on_update(self, sender, label):
        self._updated.append(label)


#################################################################
# Givens


@given(u'an empty graph')
def step_impl(context):
    context.graph = graphcat.Graph()


@given(u'a log')
def step_impl(context):
    context.log = unittest.mock.Mock()


@given(u'a graph logger')
def step_impl(context):
    context.logger = graphcat.Logger(context.graph, log=context.log)


@given(u'a graph logger with detailed outputs disabled')
def step_impl(context):
    context.logger = graphcat.Logger(context.graph, log_exceptions=False, log_inputs=False, log_outputs=False, log=context.log)

#################################################################
# Whens

class NodeOutput(object):
    def __init__(self, graph):
        self._graph = graph

    def __call__(self, label):
        return self._graph.output(label)


@when(u'adding a variable task {label} with value {value}')
def step_impl(context, label, value):
    label = eval(label)
    value = eval(value)
    context.events = EventRecorder(context.graph)

    if not hasattr(context, "variables"):
        context.variables = {}

    context.variables[label] = graphcat.VariableTask(context.graph, label, value)


@when(u'changing the variable task {label} to value {value}')
def step_impl(context, label, value):
    label = eval(label)
    value = eval(value)
    context.events = EventRecorder(context.graph)
    context.variables[label].set(value)


@when(u'adding an expression task {label} with expression {expression}')
def step_impl(context, label, expression):
    label = eval(label)
    expression = eval(expression)
    context.events = EventRecorder(context.graph)

    if not hasattr(context, "expressions"):
        context.expressions = {}

    locals = {"out": NodeOutput(context.graph)}
    context.expressions[label] = graphcat.ExpressionTask(context.graph, label, expression, locals)


@when(u'changing the expression task {label} to expression {expression}')
def step_impl(context, label, expression):
    label = eval(label)
    expression = eval(expression)
    context.events = EventRecorder(context.graph)

    locals = {"out": NodeOutput(context.graph)}
    context.expressions[label].set(expression, locals)


@when(u'adding tasks {labels} with functions {functions}')
def step_impl(context, labels, functions):
    labels = eval(labels)
    functions = eval(functions)
    context.events = EventRecorder(context.graph)
    for label, function in zip(labels, functions):
        context.graph.add_task(label, function)


@when(u'adding task {label} an exception should be raised')
def step_impl(context, label):
    label = eval(label)
    context.events = EventRecorder(context.graph)
    with test.assert_raises(ValueError):
        context.graph.add_task(label)


@when(u'adding relationship {relationship} an exception should be raised')
def step_impl(context, relationship):
    source, target = eval(relationship)
    context.events = EventRecorder(context.graph)
    with test.assert_raises(ValueError):
        context.graph.add_relationship(source, target)


@when(u'adding relationships {relationships} to inputs {inputs}')
def step_impl(context, relationships, inputs):
    relationships = eval(relationships)
    inputs = eval(inputs)
    context.events = EventRecorder(context.graph)
    for (source, target), input in zip(relationships, inputs):
        context.graph.add_relationship(source, target, input=input)


@when(u'adding relationships {relationships}')
def step_impl(context, relationships):
    relationships = eval(relationships)
    context.events = EventRecorder(context.graph)
    for source, target in relationships:
        context.graph.add_relationship(source, target)


@when(u'setting relationship {relationships} inputs to {inputs}')
def step_impl(context, relationships, inputs):
    relationships = eval(relationships)
    inputs = eval(inputs)
    context.events = EventRecorder(context.graph)
    for (source, target), input in zip(relationships, inputs):
        context.graph.set_input(source, target, input=input)


@when(u'adding tasks {labels}')
def step_impl(context, labels):
    labels = eval(labels)
    context.events = EventRecorder(context.graph)
    for label in labels:
        context.graph.add_task(label)


@when(u'updating task {label}')
def step_impl(context, label):
    label = eval(label)
    context.events = EventRecorder(context.graph)
    context.graph.update(label)


@when(u'relabelling tasks {oldlabels} as {newlabels}')
def step_impl(context, oldlabels, newlabels):
    oldlabels = eval(oldlabels)
    newlabels = eval(newlabels)
    context.events = EventRecorder(context.graph)
    for oldlabel, newlabel in zip(oldlabels, newlabels):
        context.graph.relabel_task(oldlabel, newlabel)


@when(u'removing relationship {relationship} an exception should be raised')
def step_impl(context, relationship):
    source, target = eval(relationship)
    context.events = EventRecorder(context.graph)
    with test.assert_raises(ValueError):
        context.graph.remove_relationship(source, target)


@when(u'removing relationships {relationships}')
def step_impl(context, relationships):
    relationships = eval(relationships)
    context.events = EventRecorder(context.graph)
    for source, target in relationships:
        context.graph.remove_relationship(source, target)


@when(u'updating tasks {labels}')
def step_impl(context, labels):
    labels = eval(labels)
    context.events = EventRecorder(context.graph)
    for label in labels:
        context.graph.update(label)


@when(u'removing tasks {labels}')
def step_impl(context, labels):
    labels = eval(labels)
    context.events = EventRecorder(context.graph)
    for label in labels:
        context.graph.remove_task(label)


@when(u'the task {label} function is changed to {function}')
def step_impl(context, label, function):
    label = eval(label)
    function = eval(function)
    context.events = EventRecorder(context.graph)
    context.graph.set_task_fn(label, function)


#################################################################
# Thens

@then(u'the graph should contain tasks {labels}')
def step_impl(context, labels):
    labels = eval(labels)
    for label in labels:
	    test.assert_true(context.graph._graph.has_node(label))


@then(u'the graph should contain relationships {relationships}')
def step_impl(context, relationships):
    relationships = eval(relationships)
    for source, target in relationships:
        test.assert_true(context.graph._graph.has_edge(target, source))


@then(u'the outputs of tasks {labels} should be {outputs}')
def step_impl(context, labels, outputs):
    labels = eval(labels)
    outputs = eval(outputs)
    for label, output in zip(labels, outputs):
        test.assert_equal(context.graph.output(label), output)


@then(u'the tasks {labels} should be failed')
def step_impl(context, labels):
    labels = eval(labels)
    for label in labels:
        test.assert_equal(context.graph.state(label), graphcat.TaskState.FAILED)


@then(u'the tasks {labels} should be finished')
def step_impl(context, labels):
    labels = eval(labels)
    for label in labels:
        test.assert_equal(context.graph.state(label), graphcat.TaskState.FINISHED)


@then(u'the tasks {labels} should be unfinished')
def step_impl(context, labels):
    labels = eval(labels)
    for label in labels:
        test.assert_equal(context.graph.state(label), graphcat.TaskState.UNFINISHED)


@then(u'tasks {labels} are updated')
def step_impl(context, labels):
    labels = eval(labels)
    test.assert_equal(labels, context.events.updated)


@then(u'tasks {labels} are executed with inputs {inputs}')
def step_impl(context, labels, inputs):
    labels = eval(labels)
    inputs = eval(inputs)
    test.assert_equal(labels, context.events.executed)
    test.assert_equal(inputs, context.events.inputs)


@then(u'tasks {labels} are executed')
def step_impl(context, labels):
    labels = eval(labels)
    test.assert_equal(labels, context.events.executed)


@then(u'tasks {labels} are finished')
def step_impl(context, labels):
    labels = eval(labels)
    test.assert_equal(labels, context.events.finished)


@then(u'the task {labels} outputs should be {outputs}')
def step_impl(context, labels, outputs):
    labels = eval(labels)
    outputs = eval(outputs)
    for label, output in zip(labels, outputs):
        test.assert_equal(context.graph.output(label), output)


@then(u'the log should contain {calls}')
def step_impl(context, calls):
    calls = eval(calls)

    calls = [(call[0], (call[1],), {}) for call in calls]
    mock_calls = [tuple(call) for call in context.logger._log.mock_calls]
    test.assert_equal(calls, mock_calls)
    context.logger._log.reset_mock()


@then(u'displaying the graph in a notebook should produce a visualization')
def step_impl(context):
    graphcat.notebook.display(context.graph)


