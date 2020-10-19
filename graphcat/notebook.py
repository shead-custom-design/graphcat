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

"""Integration with Jupyter notebooks, https://jupyter.org"""

import IPython.display
import pygraphviz

import graphcat


def display(graph):
    """Display a :class:`graphcat.Graph` inline in a Jupyter notebook.

    This is extremely useful for understanding and debugging graphs.  The
    structure and current state of the graph is displayed as an inline SVG
    graphic.  Each task is rendered as a box with the task label.  Arrows are
    drawn between tasks, pointing from upstream producers of data to downstream
    consumers.  Arrows are labelled to show named inputs, if any.  The color of
    each box shows its state: white for unfinished tasks, red for tasks that
    are failed, and black for tasks that are finished.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        The graph to be visualized.
    """

    black = "#494744"
    red = "crimson"
    white = "white"

    agraph = pygraphviz.AGraph(directed=True, strict=False, ranksep="0.4")
    agraph.node_attr.update(fontname="Helvetica", fontsize=8, shape="box", style="filled", margin="0.08,0.04", width="0.4", height="0")
    agraph.edge_attr.update(fontname="Helvetica", fontsize=8, color=black)

    for node in graph._graph.nodes():
        if graph._graph.nodes[node]["state"] == graphcat.TaskState.UNFINISHED:
            color = black
            fontcolor = black
            fillcolor = white
        if graph._graph.nodes[node]["state"] == graphcat.TaskState.FAILED:
            color = red
            fontcolor = white
            fillcolor = red
        if graph._graph.nodes[node]["state"] == graphcat.TaskState.FINISHED:
            color = black
            fontcolor = white
            fillcolor = black

        agraph.add_node(node, color=color, fillcolor=fillcolor, fontcolor=fontcolor)

    for target, source, input in graph._graph.edges(data="input"):
        if input is None:
            input = ""
        agraph.add_edge(source, target, label=input) # We want edges to point from dependencies to dependents.

    IPython.display.display(IPython.display.SVG(data=agraph.draw(prog="dot", format="svg")))
