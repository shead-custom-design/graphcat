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
    """Display a graphcat graph inline in a Jupyter notebook.

    This is extremely useful for debugging graphs.  The structure and current
    state of the graph is displayed as an inline SVG graphic.  Each graph
    node is rendered as a box with the node's label.  Arrows are drawn
    between nodes, pointing from upstream producers of data to downstream
    consumers.  Arrows are labelled with their role, if any.  The color of each box
    shows its state: white for outdated nodes, red for nodes that are outdated
    due to an error, and light gray for nodes that are ready.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        The graph to be visualized.
    """

    black = "#494744"
    red = "crimson"
    white = "white"

    agraph = pygraphviz.AGraph(directed=True, strict=False, ranksep="0.4")
    agraph.node_attr.update(fontname="Helvetica", shape="box", style="filled", margin="0.1,0.05", width="0.4", height="0")
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

    for edge in graph._graph.edges():
        input = graph._graph.edges[edge]["input"]
        if input == graphcat.Input.DEFAULT:
            input = ""
        agraph.add_edge(edge[1], edge[0], label=input) # We want edges to point from dependencies to dependees.

    IPython.display.display(IPython.display.SVG(data=agraph.draw(prog="dot", format="svg")))
