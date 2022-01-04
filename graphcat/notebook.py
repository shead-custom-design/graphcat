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

import graphcat.diagram
import graphcat.optional
import graphcat.require


IPython = graphcat.optional.module("IPython.display")


@graphcat.require.loaded_module("IPython.display")
def display(graph, hide=None, rankdir="LR"):
    """Display a computational graph inline in a Jupyter notebook.

    This is extremely useful for understanding and debugging graphs.  The
    structure and current state of the graph is displayed as an inline SVG
    graphic.  See :func:`graphcat.diagram.draw` for details.

    Parameters
    ----------
    graph: :class:`graphcat.Graph` or :class:`pygraphviz.AGraph`, required
        The graph to be visualized.
    hide: Python callable, optional
        Python callable that can be used to hide tasks in the displayed figure.
        If :any:`None` (the default), all tasks will be displayed.  Ignored if
        `graph` is a :class:`pygraphviz.AGraph`.
    rankdir: :class:`str`, optional
        Graphviz rankdir attribute that determines the direction of data flow
        within the diagram.  Default: ``"LR"``, which is left-to-right flow.
        Ignored if `graph` is a :class:`pygraphviz.AGraph`.
    """

    agraph = graphcat.diagram.draw(graph, hide=hide, rankdir=rankdir)
    IPython.display.display(IPython.display.SVG(data=agraph.draw(prog="dot", format="svg")))
