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

"""Functionality for drawing diagrams of computational graphs."""

try:
    import pygraphviz
except: # pragma: no cover
    pass

import graphcat.require


@graphcat.require.loaded_module("pygraphviz")
def draw(graph, hide=None, rankdir="LR"):
    """Create a diagram of a computational graph.

    This is extremely useful for understanding and debugging computational
    graphs.  The structure and current state is converted to a PyGraphviz
    graph.  By default, each task is rendered as a box with the task label.
    Arrows are drawn between tasks, pointing from upstream producers of data to
    downstream consumers.  Arrows are labelled to show named inputs, if any.
    The color of each box shows its state: white for unfinished tasks, red for
    tasks that are failed, and black for tasks that are finished.

    Callers can customize the appearance of the graph by modifying the result
    before rendering it to an image or Jupyter notebook.

    Parameters
    ----------
    graph: :class:`graphcat.graph.Graph` derivative or :class:`pygraphviz.AGraph`, required
        The graph to be visualized.
    hide: Python callable, optional
        Python callable that can be used to hide tasks in the displayed figure.
        If :any:`None` (the default), all tasks will be displayed.  Ignored if
        `graph` is an instance of :class:`pygraphviz.AGraph`.
    rankdir: :class:`str`, optional
        Graphviz rankdir attribute that determines the direction of data flow
        within the diagram.  Default: ``"LR"``, which is left-to-right flow.
        Ignored if `graph` is an instance of :class:`pygraphviz.AGraph`.

    Returns
    -------
    diagram: :class:`pygraphviz.AGraph`
        Diagrammatic representation of `graph`.  Callers can modify `diagram`
        as needed before using its layout and drawing methods to produce a
        final image.

    See Also
    --------
    :func:`graphcat.notebook.display` - displays a graph in a Jupyter notebook.
    """

    if isinstance(graph, pygraphviz.AGraph):
        return graph

    if hide is None:
        hide = none

    nodes = [node for node in graph._graph.nodes() if not hide(graph, node)]
    subgraph = graph._graph.subgraph(nodes)

    black = "#494744"
    red = "crimson"
    white = "white"

    edgestyle = "solid"
    arrowhead = "lnormal" if graph.is_streaming else "normal"
    arrowhead = "o" + arrowhead if graph.is_dynamic else arrowhead

    agraph = pygraphviz.AGraph(directed=True, strict=False, ranksep="0.4", rankdir=rankdir)
    agraph.node_attr.update(fontname="Helvetica", fontsize=8, shape="box", style="filled", margin="0.08,0.04", width="0.4", height="0")
    agraph.edge_attr.update(fontname="Helvetica", fontsize=8, color=black, arrowhead=arrowhead, style=edgestyle)

    for node in subgraph.nodes():
        if subgraph.nodes[node]["state"] == graphcat.TaskState.UNFINISHED:
            color = black
            fontcolor = black
            fillcolor = white
        if subgraph.nodes[node]["state"] == graphcat.TaskState.FAILED:
            color = red
            fontcolor = white
            fillcolor = red
        if subgraph.nodes[node]["state"] == graphcat.TaskState.FINISHED:
            color = black
            fontcolor = white
            fillcolor = black

        agraph.add_node(node, color=color, fillcolor=fillcolor, fontcolor=fontcolor)

    for target, source, input in subgraph.edges(data="input"):
        if input is None:
            input = ""
        agraph.add_edge(source, target, label=f"  {input}  ") # We want edges to point from dependencies to dependents.

    return agraph


def leaves(graph, node):
    """Filter function that hides all leaf nodes when displaying a graph using :func:`draw`."""
    return graph._graph.out_degree(node) == 0


def none(graph, node):
    """Do-nothing filter function used to display an entire graph using :func:`draw`."""
    return False


def performance(agraph, monitor):
    """Add performance monitor information to a graph diagram.

    Parameters
    ----------
    agraph: :class:`pygraphviz.AGraph`, required
        Diagram originally created using :func:`draw`.
    monitor: :class:`graphcat.common.PerformanceMonitor`, required
        Performance monitor object containing performance results to be
        added to `agraph`

    Returns
    -------
    diagram: :class:`pygraphviz.AGraph`
        Input diagram supplemented with performance results from `monitor`.
    """
    all_times = [times[-1] for times in monitor.tasks.values()]
    min_time = min(all_times)
    max_time = max(all_times)

    agraph = agraph.copy()
    agraph.graph_attr["forcelabels"] = True
    for name, times in monitor.tasks.items():
        time = times[-1]
        if max_time - min_time > 0:
            percent = (time - min_time) / (max_time - min_time)
            if percent > 0.66:
                timecolor = "red"
            elif percent > 0.33:
                timecolor = "#ffaa00"
            else:
                timecolor = "green"
        else:
            timecolor="black"
        agraph.get_node(name).attr["xlabel"] = f"<<font color='{timecolor}'>&#11044;</font> <font color='black'>{time:.4f}s</font>>"
    return agraph


