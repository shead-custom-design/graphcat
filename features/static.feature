Feature: Static Graphs

    Scenario: Empty Graph
        Given an empty static graph
        Then the graph should contain tasks []
        And the graph should contain links []


    Scenario Outline: Adding Links
        Given an empty static graph
        When adding tasks <tasks>
        And adding links <links>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain links <links>
        And the task <finished before> state is finished
        And the task <unfinished before> state is unfinished
        When adding links <added links>
        Then the graph should contain tasks <new tasks>
        And the graph should contain links <new links>
        And the task <finished after> state is finished
        And the task <unfinished after> state is unfinished

        Examples:
            | tasks           | links                 | update tasks | finished before | unfinished before |  added links          | new tasks       | new links                                | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None))]  | ["A", "B"]   | ["A", "B"]      | ["C"]             |  [("C", ("B", None))] | ["A", "B", "C"] | [("A", ("B", None)), ("C", ("B", None))] | ["A"]           | ["B", "C"]       |

        Examples: Parallel Edges
            | tasks           | links                 | update tasks | finished before | unfinished before |  added links          | new tasks       | new links                                | finished after  | unfinished after |
            | ["A", "B"]      | [("A", ("B", 0))]     | ["A", "B"]   | ["A", "B"]      | []                |  [("A", ("B", 1))]    | ["A", "B"]      | [("A", ("B", 0)), ("A", ("B", 1))]       | ["A"]           | ["B"]            |


    Scenario Outline: Adding Tasks
        Given an empty static graph
        When adding tasks <tasks>
        And adding links <links>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain links <links>
        And the task <finished before> state is finished
        And the task <unfinished before> state is unfinished
        When adding tasks <added tasks>
        Then the graph should contain tasks <new tasks>
        And the graph should contain links <new links>
        And the task <finished after> state is finished
        And the task <unfinished after> state is unfinished

        Examples:
            | tasks      | links                 | update tasks | finished before | unfinished before |  added tasks       | new tasks       | new links                 | finished after  | unfinished after |
            | ["A", "B"] | [("A", ("B", None))]  | ["A", "B"]   | ["A", "B"]      | []                |  ["C"]             | ["A", "B", "C"] | [("A", ("B", None))]      | ["A", "B"]      | ["C"]            |


    Scenario Outline: Renaming Tasks
        Given an empty static graph
        When adding tasks <tasks>
        And adding links <links>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain links <links>
        And the task <finished before> state is finished
        And the task <unfinished before> state is unfinished
        When renaming tasks <old names> as <new names>
        Then tasks <old names> should be renamed to <new names>
        Then the graph should contain tasks <new tasks>
        And the graph should contain links <new links>
        And the task <finished after> state is finished
        And the task <unfinished after> state is unfinished

        Examples: Fan-Out
            | tasks           | links                                    | update tasks    | finished before | unfinished before | old names  | new names   | new tasks       | new links                                | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["A"]      | ["D"]       | ["D", "B", "C"] | [("D", ("B", None)), ("D", ("C", None))] | []              | ["D", "B", "C"]  |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["B"]      | ["D"]       | ["A", "D", "C"] | [("A", ("D", None)), ("A", ("C", None))] | ["A", "C"]      | ["D"]            |

        Examples: Fan-In
            | tasks           | links                                    | update tasks    | finished before | unfinished before | old names  | new names   | new tasks       | new links                                | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None)), ("C", ("B", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["B"]      | ["D"]       | ["A", "D", "C"] | [("A", ("D", None)), ("C", ("D", None))] | ["A", "C"]      | ["D"]            |


    Scenario Outline: Removing Links
        Given an empty static graph
        When adding tasks <tasks>
        And adding links <links>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain links <links>
        And the task <finished before> state is finished
        And the task <unfinished before> state is unfinished
        When removing links <removed>
        Then the graph should contain tasks <new tasks>
        And the graph should contain links <new links>
        And the task <finished after> state is finished
        And the task <unfinished after> state is unfinished

        Examples: Fan-Out
            | tasks           | links                                    | update tasks    | finished before | unfinished before | removed      | new tasks       | new links                | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | [("A", "B")] | ["A", "B", "C"] | [("A", ("C", None))]     | []              | ["A", "B", "C"]  |

        Examples: Fan-In
            | tasks           | links                                    | update tasks    | finished before | unfinished before | removed      | new tasks       | new links                        | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None)), ("C", ("B", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | [("A", "B")] | ["A", "B", "C"] | [("C", ("B", None))]             | ["C"]           | ["A", "B"]       |


    Scenario Outline: Removing Tasks
        Given an empty static graph
        When adding tasks <tasks>
        And adding links <links>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain links <links>
        And the task <finished before> state is finished
        And the task <unfinished before> state is unfinished
        When removing tasks <removed> with <api>
        Then the graph should contain tasks <new tasks>
        And the graph should contain links <new links>
        And the task <finished after> state is finished
        And the task <unfinished after> state is unfinished

        Examples: Fan-Out
            | tasks           | links                                    | update tasks    | finished before | unfinished before | removed    | api             | new tasks       | new links                | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["A"]      | clear_tasks     | ["B", "C"]      | []                       | []              | ["B", "C"]       |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["B"]      | clear_tasks     | ["A", "C"]      | [("A", ("C", None))]     | ["A", "C"]      | []               |

        Examples: Fan-In
            | tasks           | links                                    | update tasks    | finished before | unfinished before | removed    | api             | new tasks       | new links                | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None)), ("C", ("B", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["A"]      | clear_tasks     | ["B", "C"]      | [("C", ("B", None))]     | ["C"]           | ["B"]            |
            | ["A", "B", "C"] | [("A", ("B", None)), ("C", ("B", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["B"]      | clear_tasks     | ["A", "C"]      | []                       | ["A", "C"]      | []               |


    Scenario Outline: Setting Parameters
        Given an empty static graph
        When adding tasks <tasks>
        And setting parameter <target> <input> <source> <value>
        Then the graph should contain tasks <result tasks>
        And the graph should contain links <result links>

        Examples:
            | tasks      | target     | input        | source       | value          |  result tasks        | result links                |
            | ["A"]      | "A"        | None         | "A/B"        | "foo"          |  ["A", "A/B"]        | [("A/B", ("A", None))]      |
            | ["A"]      | "A"        | 0            | "A/B"        | "foo"          |  ["A", "A/B"]        | [("A/B", ("A", 0))]         |


    Scenario Outline: Updating Tasks
        Given an empty static graph
        When adding tasks <tasks>
        And adding links <links>
        Then the graph should contain tasks <tasks>
        And the graph should contain links <links>
        When updating tasks <update tasks>
        Then tasks <updated> are updated
        And tasks <executed> are executed
        And tasks <finished> are finished
        And the task <finished tasks> state is finished
        And the task <unfinished tasks> state is unfinished

        Examples: Fan-Out
            | tasks           | links                                    | update tasks | updated              | executed        | finished        | finished tasks  | unfinished tasks |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | []           | []                   | []              | []              | []              | ["A", "B", "C"]  |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["A"]        | ["A"]                | ["A"]           | ["A"]           | ["A"]           | ["B", "C"]       |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["A", "A"]   | ["A", "A"]           | ["A"]           | ["A"]           | ["A"]           | ["B", "C"]       |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["B"]        | ["A", "B"]           | ["A", "B"]      | ["A", "B"]      | ["A", "B"]      | ["C"]            |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["B", "C"]   | ["A", "B", "A", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | []               |

        Examples: Fan-In
            | tasks           | links                                    | update tasks | updated              | executed        | finished        | finished tasks  | unfinished tasks |
            | ["A", "B", "C"] | [("A", ("C", None)), ("B", ("C", None))] | []           | []                   | []              | []              | []              | ["A", "B", "C"]  |
            | ["A", "B", "C"] | [("A", ("C", None)), ("B", ("C", None))] | ["A"]        | ["A"]                | ["A"]           | ["A"]           | ["A"]           | ["B", "C"]       |
            | ["A", "B", "C"] | [("A", ("C", None)), ("B", ("C", None))] | ["C"]        | ["A", "B", "C"]      | ["A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | []               |
            | ["A", "B", "C"] | [("A", ("C", None)), ("B", ("C", None))] | ["C", "A"]   | ["A", "B", "C", "A"] | ["A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | []               |


    Scenario Outline: Task Functions
        Given an empty static graph
        When adding tasks <tasks> with functions <functions>
        And computing the task <tasks> outputs
        Then the outputs should be <outputs>

        Examples:
            | tasks     | functions                               | outputs       |
            | ["A"]     | [None]                                  | [None]        |
            | ["A"]     | [graphcat.null]                         | [None]        |
            | ["A"]     | [graphcat.constant(2)]                  | [2]           |
            | ["A"]     | [graphcat.constant(3.14)]               | [3.14]        |
            | ["A"]     | [graphcat.constant("foo")]              | ["foo"]       |
            | ["A"]     | [graphcat.constant(("foo", 7))]         | [("foo", 7)]  |
            | ["A"]     | [graphcat.execute("2 + 3")]             | [5]           |
            | ["A"]     | [graphcat.execute("2 * 3")]             | [6]           |
            | ["A"]     | [graphcat.execute("'foo' + 'bar'")]     | ["foobar"]    |


    Scenario: Failing Task Function
        Given an empty static graph
        When adding tasks ["A", "B", "C"] with functions [graphcat.null, graphcat.raise_exception(RuntimeError()), graphcat.null]
        And adding links [("A", "B"), ("B", "C")]
        And updating task "C" an exception should be raised
        Then the task ["A"] state is finished
        And the task ["B", "C"] state is failed


    Scenario: Adding Duplicate Tasks
        Given an empty static graph
        When adding tasks ["A", "B", "C"]
        And adding links [("A", "B"), ("B", "C")]
        And adding task "A" an exception should be raised
        Then tasks [] are updated
        And the graph should contain tasks ["A", "B", "C"]
        And the graph should contain links [("A", ("B", None)), ("B", ("C", None))]


    Scenario: Adding Link To Nonexistent Task
        Given an empty static graph
        When adding tasks ["A", "B", "C"]
        And adding links [("A", "B"), ("B", "C")]
        And adding link ("A", "D") an exception should be raised
        Then tasks [] are updated
        And the graph should contain tasks ["A", "B", "C"]
        And the graph should contain links [("A", ("B", None)), ("B", ("C", None))]


    Scenario: Removing Nonexistent Link
        Given an empty static graph
        When adding tasks ["A", "B", "C"]
        And adding links [("A", "B"), ("B", "C")]
        And removing link ("A", "C") no exception should be raised
        Then the graph should contain tasks ["A", "B", "C"]
        And the graph should contain links [("A", ("B", None)), ("B", ("C", None))]


    Scenario: Changing Task Functions
        Given an empty static graph
        When adding tasks ["A", "B", "C"] with functions [graphcat.constant(1), graphcat.constant(2), graphcat.constant(3)]
        And adding links [("A", "B"), ("B", "C")]
        And computing the task ["A", "B", "C"] outputs
        Then the task ["A", "B", "C"] state is finished
        And the outputs should be [1, 2, 3]
        When the task "B" function is changed to graphcat.null
        Then the task ["A"] state is finished
        And the task ["B", "C"] state is unfinished
        When computing the task ["A", "B", "C"] outputs
        Then the outputs should be [1, None, 3]


    Scenario: Expression Tasks
        Given an empty static graph
        When adding tasks ["A", "B", "choice"] with functions [graphcat.constant(1), graphcat.constant(2), graphcat.constant(True)]
        And adding an expression task "expr" with expression "3+4"
        Then the graph should contain tasks ["A", "B", "choice", "expr"]
        And the graph should contain links []
        And the task ["A", "B", "choice", "expr"] state is unfinished
        And the graph should contain links []
        When computing the task ["expr"] outputs
        Then the outputs should be [7]
        When changing the expression task "expr" to expression "out('A') if out('choice') else out('B')"
        And computing the task ["expr"] outputs
        Then the outputs should be [1]
        And the graph should contain links [("A", ("expr", graphcat.Input.AUTODEPENDENCY)), ("choice", ("expr", graphcat.Input.AUTODEPENDENCY))]
        When the task "A" function is changed to graphcat.constant(3)
        And computing the task ["expr"] outputs
        Then the outputs should be [3]
        When the task "choice" function is changed to graphcat.constant(False)
        And computing the task ["expr"] outputs
        Then the outputs should be [2]
        And the graph should contain links [("B", ("expr", graphcat.Input.AUTODEPENDENCY)), ("choice", ("expr", graphcat.Input.AUTODEPENDENCY))]
        When the task "B" function is changed to graphcat.constant(4)
        And computing the task ["expr"] outputs
        Then the outputs should be [4]
        When renaming tasks ["B"] as ["C"]
        Then the graph should contain tasks ["A", "C", "choice", "expr"]
        And the graph should contain links [("C", ("expr", graphcat.Input.AUTODEPENDENCY)), ("choice", ("expr", graphcat.Input.AUTODEPENDENCY))]
        When changing the expression task "expr" to expression "out('A') if out('choice') else out('C')"
        And computing the task ["expr"] outputs
        Then the outputs should be [4]
        When renaming tasks ["expr"] as ["expression"]
        Then the graph should contain tasks ["A", "C", "choice", "expression"]
        And the graph should contain links [("C", ("expression", graphcat.Input.AUTODEPENDENCY)), ("choice", ("expression", graphcat.Input.AUTODEPENDENCY))]
        When computing the task ["expression"] outputs
        Then the outputs should be [4]


    Scenario: Graph Logger
        Given an empty static graph
        And a log
        And a graph logger
        When adding tasks ["A"]
        And updating tasks ["A"]
        Then the log should contain [("info", "Task A updating."), ("info", "Task A executing. Inputs: {}"), ("info", "Task A finished. Output: None")]
        When adding tasks ["B"] with functions [graphcat.raise_exception(RuntimeError("Whoops!"))]
        And updating task "B" an exception should be raised
        Then the log should contain [("info", "Task B updating."), ("info", "Task B executing. Inputs: {}"), ("error", "Task B failed. Exception: Whoops!")]


    Scenario: Simplified Graph Logger
        Given an empty static graph
        And a log
        And a graph logger with detailed outputs disabled
        When adding tasks ["A"]
        And updating tasks ["A"]
        Then the log should contain [("info", "Task A updating."), ("info", "Task A executing."), ("info", "Task A finished.")]
        When adding tasks ["B"] with functions [graphcat.raise_exception(RuntimeError("Whoops!"))]
        And updating task "B" an exception should be raised
        Then the log should contain [("info", "Task B updating."), ("info", "Task B executing."), ("error", "Task B failed.")]


    Scenario: Diagrams
        Given the pygraphviz module is available
        And an empty static graph
        When adding tasks ["A", "B", "C", "D"] with functions [None, None, None, graphcat.raise_exception(RuntimeError("Whoops!"))]
        And adding links [("A", "B"), ("A", "C"), ("B", "D")]
        And updating task "D" an exception should be raised
        Then the graph can be drawn as a diagram


    Scenario: Diagram Subgraphs
        Given an empty static graph
        When adding tasks ["A", "B", "C", "D"]
        And adding links [("A", "B"), ("C", "B"), ("B", "D")]
        When filtering the graph with graphcat.diagram.leaves then the remaining nodes should match ["B", "D"]


    Scenario: Notebook Display
        Given the pygraphviz module is available
        And the IPython module is available
        And an empty static graph
        When adding tasks ["A", "B", "C", "D"] with functions [None, None, None, graphcat.raise_exception(RuntimeError("Whoops!"))]
        And adding links [("A", "B"), ("A", "C"), ("B", "D")]
        And updating task "D" an exception should be raised
        Then displaying the graph in a notebook should produce a visualization
        When the graph is converted to a diagram
        Then the diagram can be displayed in a notebook


    Scenario: Named Inputs
        Given an empty static graph
        When adding tasks ["A", "B", "C", "D"] with functions [graphcat.constant(2), graphcat.constant(3), graphcat.constant(4), None]
        And adding links [("A", ("D", 0)), ("B", ("D", 1)), ("C", ("D", 1))]
        And updating tasks ["D"]
        Then tasks ["A", "B", "C", "D"] are executed
        And task "A" has 0 inputs
        And task "D" has 3 inputs
        And the task "D" inputs contain 0
        And the task "D" inputs contain 1
        And the task "D" inputs do not contain 2
        And getting input 0 from task "D" returns 2
        And getting input 1 from task "D" raises KeyError
        And getting input 2 from task "D" returns None
        And getting one input from task "D" input 0 returns 2
        And getting one input from task "D" input 1 raises KeyError
        And getting one input from task "D" input 2 raises KeyError
        And getting all inputs from task "D" input 0 returns [2]
        And getting all inputs from task "D" input 1 returns [3, 4]
        And getting all inputs from task "D" input 2 returns []
        And getting the task "D" input keys returns [0, 1, 1]
        And getting the task "D" input values returns [2, 3, 4]
        And getting the task "D" input items returns [(0, 2), (1, 3), (1, 4)]


    Scenario: Retrieving Task Links
        Given an empty static graph
        When adding tasks ["A", "B", "C"]
        And adding links [("A", ("C", "lhs")), ("B", ("C", "rhs"))]
        And adding links [("A", ("B", None))]
        Then the graph should contain links [("A", ("B", None)), ("A", ("C", "lhs")), ("B", ("C", "rhs"))]
        And tasks ["A"] should have links [("A", ("B", None)), ("A", ("C", "lhs"))]
        And tasks ["B", "C"] should have links [("B", ("C", "rhs"))]


    Scenario: Setting Links
        Given an empty static graph
        When adding tasks ["A", "B", "C", "D"]
        And adding links [("A", "B"), ("A", "C")]
        Then the graph should contain links [("A", ("B", None)), ("A", ("C", None))]
        When setting links [("A", ["C", "D"])]
        Then the graph should contain links [("A", ("C", None)), ("A", ("D", None))]
        When setting links [("A", ("B", None))]
        Then the graph should contain links [("A", ("B", None))]
        When setting links [("A", ("B", "foo"))]
        Then the graph should contain links [("A", ("B", "foo"))]


    Scenario: Membership
        Given an empty static graph
        When adding tasks ["A", "B"]
        Then the graph should contain tasks ["A", "B"]
        And testing if the graph contains task "A" should return True
        And testing if the graph contains task "C" should return False


    Scenario: Passthrough
        Given an empty static graph
        When adding tasks ["A", "B", "C"] with functions [graphcat.constant(42), graphcat.constant(10), graphcat.passthrough("lhs")]
        And adding links [("A", ("C", "lhs")), ("B", ("C", "rhs"))]
        And computing the task ["A", "B", "C"] outputs
        Then the outputs should be [42, 10, 42]


    Scenario: Performance Monitor
        Given an empty static graph
        And a performance monitor
        When adding tasks ["A", "B", "C"] with functions [graphcat.delay(0.3), graphcat.delay(0.2), graphcat.delay(0.1)]
        And adding links [("A", "B"), ("B", "C")]
        And updating tasks ["C"]
        Then the performance monitor output should be {"A": [0.3], "B": [0.2], "C": [0.1]}
        When tasks ["C"] are marked unfinished
        And updating tasks ["C"]
        Then the performance monitor output should be {"A": [0.3], "B": [0.2], "C": [0.1, 0.1]}
        When the performance monitor is reset
        Then the performance monitor output should be {}


    Scenario: Performance Monitor Diagram
        Given the pygraphviz module is available
        And an empty static graph
        And a performance monitor
        When adding tasks ["A", "B", "C"] with functions [graphcat.delay(0.3), graphcat.delay(0.2), graphcat.delay(0.1)]
        And adding links [("A", "B"), ("B", "C")]
        And updating tasks ["C"]
        Then the performance monitor output should be {"A": [0.3], "B": [0.2], "C": [0.1]}
        And the graph can be drawn as a diagram with performance overlay


    Scenario: Suppress array Updates
        Given the numpy module is available
        And an empty static graph
        When adding tasks ["A"] with functions [graphcat.array(numpy.arange(4))]
        And computing the task ["A"] outputs
        Then the task ["A"] state is finished
        And the numpy outputs should be [[0, 1, 2, 3]]
        When the task "A" function is changed to graphcat.array(numpy.arange(3))
        Then the task ["A"] state is unfinished
        When computing the task ["A"] outputs
        Then the numpy outputs should be [[0, 1, 2]]
        When the task "A" function is changed to graphcat.array(numpy.arange(3))
        Then the task ["A"] state is finished
        When computing the task ["A"] outputs
        Then the numpy outputs should be [[0, 1, 2]]


    Scenario: Suppress constant Updates
        Given an empty static graph
        When adding tasks ["A"] with functions [graphcat.constant(1)]
        And computing the task ["A"] outputs
        Then the task ["A"] state is finished
        And the outputs should be [1]
        When the task "A" function is changed to graphcat.constant(2)
        Then the task ["A"] state is unfinished
        When computing the task ["A"] outputs
        Then the outputs should be [2]
        When the task "A" function is changed to graphcat.constant(2)
        Then the task ["A"] state is finished
        When computing the task ["A"] outputs
        Then the outputs should be [2]


    Scenario: Suppress passthrough Updates
        Given an empty static graph
        When adding tasks ["A", "B", "C"] with functions [graphcat.constant("a"), graphcat.constant("b"), graphcat.passthrough(0)]
        And adding links [("A", ("C", 0)), ("B", ("C", 1))]
        And computing the task ["C"] outputs
        Then the task ["A", "B", "C"] state is finished
        And the outputs should be ["a"]
        When the task "C" function is changed to graphcat.passthrough(1)
        Then the task ["A", "B"] state is finished
        And the task ["C"] state is unfinished
        When computing the task ["C"] outputs
        Then the outputs should be ["b"]
        When the task "C" function is changed to graphcat.passthrough(1)
        Then the task ["A", "B", "C"] state is finished
        When computing the task ["C"] outputs
        Then the outputs should be ["b"]


    Scenario: Cycles
        Given an empty static graph
        When adding tasks ["A", "B", "C"] with functions [graphcat.passthrough(), graphcat.passthrough(), graphcat.passthrough()]
        And adding links [("A", "B"), ("B", "C"), ("C", "A")]
        Then the task ["A", "B", "C"] state is unfinished
        When computing the task ["C"] outputs
        Then tasks ["A", "B", "C"] are updated
        And tasks ["A", "B", "C"] are executed
        And tasks ["A", "B", "C"] are finished
        And tasks [] detect cycles
        And the outputs should be [None]

