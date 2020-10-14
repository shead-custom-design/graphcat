Feature: Graph


    Scenario: Empty Graph
        Given an empty graph
        Then the graph should contain tasks []
        And the graph should contain links []


    Scenario Outline: Adding Links
        Given an empty graph
        When adding tasks <tasks>
        And adding links <links>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain links <links>
        And the tasks <finished before> should be finished
        And the tasks <unfinished before> should be unfinished
        When adding links <added links>
        Then the graph should contain tasks <new tasks>
        And the graph should contain links <new links>
        And the tasks <finished after> should be finished
        And the tasks <unfinished after> should be unfinished

        Examples:
            | tasks           | links                 | update tasks | finished before | unfinished before |  added links          | new tasks       | new links                                | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None))]  | ["A", "B"]   | ["A", "B"]      | ["C"]             |  [("C", ("B", None))] | ["A", "B", "C"] | [("A", ("B", None)), ("C", ("B", None))] | ["A"]           | ["B", "C"]       |


    Scenario Outline: Adding Tasks
        Given an empty graph
        When adding tasks <tasks>
        And adding links <links>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain links <links>
        And the tasks <finished before> should be finished
        And the tasks <unfinished before> should be unfinished
        When adding tasks <added tasks>
        Then the graph should contain tasks <new tasks>
        And the graph should contain links <new links>
        And the tasks <finished after> should be finished
        And the tasks <unfinished after> should be unfinished

        Examples:
            | tasks      | links                 | update tasks | finished before | unfinished before |  added tasks       | new tasks       | new links                 | finished after  | unfinished after |
            | ["A", "B"] | [("A", ("B", None))]  | ["A", "B"]   | ["A", "B"]      | []                |  ["C"]             | ["A", "B", "C"] | [("A", ("B", None))]      | ["A", "B"]      | ["C"]            |


    Scenario Outline: Renaming Tasks
        Given an empty graph
        When adding tasks <tasks>
        And adding links <links>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain links <links>
        And the tasks <finished before> should be finished
        And the tasks <unfinished before> should be unfinished
        When renaming tasks <old names> as <new names> with <api>
        Then the graph should contain tasks <new tasks>
        And the graph should contain links <new links>
        And the tasks <finished after> should be finished
        And the tasks <unfinished after> should be unfinished

        Examples: Fan-Out
            | tasks           | links                                    | update tasks    | finished before | unfinished before | old names  | new names   | api            | new tasks       | new links                                | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["A"]      | ["D"]       | move_task      | ["D", "B", "C"] | [("D", ("B", None)), ("D", ("C", None))] | []              | ["D", "B", "C"]  |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["B"]      | ["D"]       | move_task      | ["A", "D", "C"] | [("A", ("D", None)), ("A", ("C", None))] | ["A", "C"]      | ["D"]            |

        Examples: Fan-In
            | tasks           | links                                    | update tasks    | finished before | unfinished before | old names  | new names   | api            | new tasks       | new links                                | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None)), ("C", ("B", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["B"]      | ["D"]       | move_task      | ["A", "D", "C"] | [("A", ("D", None)), ("C", ("D", None))] | ["A", "C"]      | ["D"]            |


    Scenario Outline: Removing Links
        Given an empty graph
        When adding tasks <tasks>
        And adding links <links>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain links <links>
        And the tasks <finished before> should be finished
        And the tasks <unfinished before> should be unfinished
        When removing links <removed>
        Then the graph should contain tasks <new tasks>
        And the graph should contain links <new links>
        And the tasks <finished after> should be finished
        And the tasks <unfinished after> should be unfinished

        Examples: Fan-Out
            | tasks           | links                                    | update tasks    | finished before | unfinished before | removed      | new tasks       | new links                | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | [("A", "B")] | ["A", "B", "C"] | [("A", ("C", None))]     | []              | ["A", "B", "C"]  |

        Examples: Fan-In
            | tasks           | links                                    | update tasks    | finished before | unfinished before | removed      | new tasks       | new links                        | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None)), ("C", ("B", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | [("A", "B")] | ["A", "B", "C"] | [("C", ("B", None))]             | ["C"]           | ["A", "B"]       |


    Scenario Outline: Removing Tasks
        Given an empty graph
        When adding tasks <tasks>
        And adding links <links>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain links <links>
        And the tasks <finished before> should be finished
        And the tasks <unfinished before> should be unfinished
        When removing tasks <removed> with <api>
        Then the graph should contain tasks <new tasks>
        And the graph should contain links <new links>
        And the tasks <finished after> should be finished
        And the tasks <unfinished after> should be unfinished

        Examples: Fan-Out
            | tasks           | links                                    | update tasks    | finished before | unfinished before | removed    | api             | new tasks       | new links                | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["A"]      | clear_tasks     | ["B", "C"]      | []                       | []              | ["B", "C"]       |
            | ["A", "B", "C"] | [("A", ("B", None)), ("A", ("C", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["B"]      | clear_tasks     | ["A", "C"]      | [("A", ("C", None))]     | ["A", "C"]      | []               |

        Examples: Fan-In
            | tasks           | links                                    | update tasks    | finished before | unfinished before | removed    | api             | new tasks       | new links                | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", ("B", None)), ("C", ("B", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["A"]      | clear_tasks     | ["B", "C"]      | [("C", ("B", None))]     | ["C"]           | ["B"]            |
            | ["A", "B", "C"] | [("A", ("B", None)), ("C", ("B", None))] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["B"]      | clear_tasks     | ["A", "C"]      | []                       | ["A", "C"]      | []               |


    Scenario Outline: Updating Tasks
        Given an empty graph
        When adding tasks <tasks>
        And adding links <links>
        Then the graph should contain tasks <tasks>
        And the graph should contain links <links>
        When updating tasks <update tasks>
        Then tasks <updated> are updated
        And tasks <executed> are executed
        And tasks <finished> are finished
        And the tasks <finished tasks> should be finished
        And the tasks <unfinished tasks> should be unfinished

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

        Examples: Cycles
            | tasks           | links                                                        | update tasks | updated                        | executed        | finished        | finished tasks  | unfinished tasks |
            | ["A", "B", "C"] | [("A", ("B", None)), ("B", ("C", None)), ("C", ("A", None))] | []           | []                             | []              | []              | []              | ["A", "B", "C"]  |
            | ["A", "B", "C"] | [("A", ("B", None)), ("B", ("C", None)), ("C", ("A", None))] | ["A"]        | ["B", "C", "A"]                | ["B", "C", "A"] | ["B", "C", "A"] | ["A", "B", "C"] | []               |
            | ["A", "B", "C"] | [("A", ("B", None)), ("B", ("C", None)), ("C", ("A", None))] | ["B"]        | ["C", "A", "B"]                | ["C", "A", "B"] | ["C", "A", "B"] | ["A", "B", "C"] | []               |
            | ["A", "B", "C"] | [("A", ("B", None)), ("B", ("C", None)), ("C", ("A", None))] | ["C"]        | ["A", "B", "C"]                | ["A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | []               |
            | ["A", "B", "C"] | [("A", ("B", None)), ("B", ("C", None)), ("C", ("A", None))] | ["C", "C"]   | ["A", "B", "C", "A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | []               |
            | ["A", "B", "C"] | [("A", ("B", None)), ("B", ("C", None)), ("C", ("A", None))] | ["C", "A"]   | ["A", "B", "C", "B", "C", "A"] | ["A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | []               |


    Scenario Outline: Task Functions
        Given an empty graph
        When adding tasks <tasks> with functions <functions>
        Then the outputs of tasks <tasks> should be <outputs>

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
        Given an empty graph
        When adding tasks ["A", "B", "C"] with functions [graphcat.null, graphcat.raise_exception(RuntimeError()), graphcat.null]
        And adding links [("A", "B"), ("B", "C")]
        And updating task "C"
        Then the tasks ["A"] should be finished
        And the tasks ["B", "C"] should be failed


    Scenario: Adding Duplicate Tasks
        Given an empty graph
        When adding tasks ["A", "B", "C"]
        And adding links [("A", "B"), ("B", "C")]
        And adding task "A" an exception should be raised
        Then tasks [] are updated
        And the graph should contain tasks ["A", "B", "C"]
        And the graph should contain links [("A", ("B", None)), ("B", ("C", None))]


    Scenario: Adding Link To Nonexistent Task
        Given an empty graph
        When adding tasks ["A", "B", "C"]
        And adding links [("A", "B"), ("B", "C")]
        And adding link ("A", "D") an exception should be raised
        Then tasks [] are updated
        And the graph should contain tasks ["A", "B", "C"]
        And the graph should contain links [("A", ("B", None)), ("B", ("C", None))]


    Scenario: Removing Nonexistent Link
        Given an empty graph
        When adding tasks ["A", "B", "C"]
        And adding links [("A", "B"), ("B", "C")]
        And removing link ("A", "C") an exception should be raised
        Then tasks [] are updated
        And the graph should contain tasks ["A", "B", "C"]
        And the graph should contain links [("A", ("B", None)), ("B", ("C", None))]


    Scenario: Changing Task Functions
        Given an empty graph
        When adding tasks ["A", "B", "C"] with functions [graphcat.constant(1), graphcat.constant(2), graphcat.constant(3)]
        And adding links [("A", "B"), ("B", "C")]
        And updating tasks ["A", "B", "C"]
        Then the tasks ["A", "B", "C"] should be finished
        And the task ["A", "B", "C"] outputs should be [1, 2, 3]
        When the task "B" function is changed to graphcat.null
        Then the tasks ["A"] should be finished
        And the tasks ["B", "C"] should be unfinished
        And the task ["A", "B", "C"] outputs should be [1, None, 3]


    Scenario: Expression Tasks
        Given an empty graph
        When adding tasks ["A", "B"] with functions [graphcat.constant(1), graphcat.constant(2)]
        And adding an expression task "C" with expression "3+4"
        And updating tasks ["A", "B", "C"]
        Then the graph should contain tasks ["A", "B", "C"]
        And the graph should contain links []
        And the tasks ["A", "B", "C"] should be finished
        And the task ["A", "B", "C"] outputs should be [1, 2, 7]
        When changing the expression task "C" to expression "out('A') + 1.1"
        Then the graph should contain links [("A", ("C", graphcat.Input.DEPENDENCY))]
        And the tasks ["A", "B", "C"] should be finished
        And the task ["A", "B", "C"] outputs should be [1, 2, 2.1]
        When the task "A" function is changed to graphcat.constant(3)
        Then the task ["A", "B", "C"] outputs should be [3, 2, 4.1]
        When changing the expression task "C" to expression "out('B') + 1.1"
        Then the graph should contain links [("B", ("C", graphcat.Input.DEPENDENCY))]
        And the task ["A", "B", "C"] outputs should be [3, 2, 3.1]


    Scenario: Variable Tasks
        Given an empty graph
        When adding a variable task "A" with value 3.14
        Then the graph should contain tasks ["A"]
        And the tasks ["A"] should be unfinished
        And the task ["A"] outputs should be [3.14]
        When changing the variable task "A" to value "foo"
        Then the tasks ["A"] should be unfinished
        And the task ["A"] outputs should be ["foo"]


    Scenario: Graph Logger
        Given an empty graph
        And a log
        And a graph logger
        When adding tasks ["A"]
        And updating tasks ["A"]
        Then the log should contain [("debug", "Task A updating."), ("info", "Task A executing. Inputs: {}"), ("info", "Task A finished. Output: None")]
        When adding tasks ["B"] with functions [graphcat.raise_exception(RuntimeError("Whoops!"))]
        And updating tasks ["B"]
        Then the log should contain [("debug", "Task B updating."), ("info", "Task B executing. Inputs: {}"), ("error", "Task B failed. Exception: Whoops!")]


    Scenario: Simplified Graph Logger
        Given an empty graph
        And a log
        And a graph logger with detailed outputs disabled
        When adding tasks ["A"]
        And updating tasks ["A"]
        Then the log should contain [("debug", "Task A updating."), ("info", "Task A executing."), ("info", "Task A finished.")]
        When adding tasks ["B"] with functions [graphcat.raise_exception(RuntimeError("Whoops!"))]
        And updating tasks ["B"]
        Then the log should contain [("debug", "Task B updating."), ("info", "Task B executing."), ("error", "Task B failed.")]


    Scenario: Notebook Display
        Given an empty graph
        When adding tasks ["A", "B", "C", "D"] with functions [None, None, None, graphcat.raise_exception(RuntimeError("Whoops!"))]
        And adding links [("A", "B"), ("A", "C"), ("B", "D")]
        And updating tasks ["D"]
        Then displaying the graph in a notebook should produce a visualization


    Scenario: Named Inputs
        Given an empty graph
        When adding tasks ["A", "B", "C"] with functions [graphcat.constant(2), graphcat.constant(3), None]
        And adding links [("A", ("C", "lhs")), ("B", ("C", "rhs"))]
        And updating tasks ["C"]
        Then tasks ["A", "B", "C"] are executed with inputs [{}, {}, {"lhs": [2], "rhs": [3]}]
        When setting links [("A", ("C", None)), ("B", ("C", None))]
        Then the tasks ["A", "B"] should be finished
        And the tasks ["C"] should be unfinished
        When updating tasks ["C"]
        Then tasks ["C"] are executed with inputs [{None: [2, 3]}]


    Scenario: Retrieving Task Links
        Given an empty graph
        When adding tasks ["A", "B", "C"]
        And adding links [("A", ("C", "lhs")), ("B", ("C", "rhs"))]
        And adding links [("A", ("B", None))]
        Then the graph should contain links [("A", ("B", None)), ("A", ("C", "lhs")), ("B", ("C", "rhs"))]
        And tasks ["A"] should have links [("A", ("B", None)), ("A", ("C", "lhs"))]
        And tasks ["B", "C"] should have links [("B", ("C", "rhs"))]


    Scenario: Setting Links
        Given an empty graph
        When adding tasks ["A", "B", "C", "D"]
        And adding links [("A", "B"), ("A", "C")]
        Then the graph should contain links [("A", ("B", None)), ("A", ("C", None))]
        When setting links [("A", ["C", "D"])]
        Then the graph should contain links [("A", ("C", None)), ("A", ("D", None))]
        When setting links [("A", ("B", None))]
        Then the graph should contain links [("A", ("B", None))]
        When setting links [("A", ("B", "foo"))]
        Then the graph should contain links [("A", ("B", "foo"))]


