Feature: Graph


    Scenario: Empty Graph
        Given an empty graph
        Then the graph should contain tasks []
        And the graph should contain relationships []


    Scenario Outline: Adding Relationships
        Given an empty graph
        When adding tasks <tasks>
        And adding relationships <relationships>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain relationships <relationships>
        And the tasks <finished before> should be finished
        And the tasks <unfinished before> should be unfinished
        When adding relationships <added relationships>
        Then the graph should contain tasks <new tasks>
        And the graph should contain relationships <new relationships>
        And the tasks <finished after> should be finished
        And the tasks <unfinished after> should be unfinished

        Examples:
            | tasks           | relationships | update tasks | finished before | unfinished before |  added relationships | new tasks       | new relationships        | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", "B")]  | ["A", "B"]   | ["A", "B"]      | ["C"]             |  [("C", "B")]        | ["A", "B", "C"] | [("A", "B"), ("C", "B")] | ["A"]           | ["B", "C"]       |


    Scenario Outline: Adding Tasks
        Given an empty graph
        When adding tasks <tasks>
        And adding relationships <relationships>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain relationships <relationships>
        And the tasks <finished before> should be finished
        And the tasks <unfinished before> should be unfinished
        When adding tasks <added tasks>
        Then the graph should contain tasks <new tasks>
        And the graph should contain relationships <new relationships>
        And the tasks <finished after> should be finished
        And the tasks <unfinished after> should be unfinished

        Examples:
            | tasks      | relationships | update tasks | finished before | unfinished before |  added tasks       | new tasks       | new relationships | finished after  | unfinished after |
            | ["A", "B"] | [("A", "B")]  | ["A", "B"]   | ["A", "B"]      | []                |  ["C"]             | ["A", "B", "C"] | [("A", "B")]      | ["A", "B"]      | ["C"]            |


    Scenario Outline: Relabelling Tasks
        Given an empty graph
        When adding tasks <tasks>
        And adding relationships <relationships>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain relationships <relationships>
        And the tasks <finished before> should be finished
        And the tasks <unfinished before> should be unfinished
        When relabelling tasks <old labels> as <new labels>
        Then the graph should contain tasks <new tasks>
        And the graph should contain relationships <new relationships>
        And the tasks <finished after> should be finished
        And the tasks <unfinished after> should be unfinished

        Examples: Fan-Out
            | tasks           | relationships            | update tasks    | finished before | unfinished before | old labels | new labels        | new tasks       | new relationships        | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", "B"), ("A", "C")] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["A"]      | ["D"]             | ["D", "B", "C"] | [("D", "B"), ("D", "C")] | []              | ["D", "B", "C"]  |
            | ["A", "B", "C"] | [("A", "B"), ("A", "C")] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["B"]      | ["D"]             | ["A", "D", "C"] | [("A", "D"), ("A", "C")] | ["A", "C"]      | ["D"]            |

        Examples: Fan-In
            | tasks           | relationships            | update tasks    | finished before | unfinished before | old labels | new labels        | new tasks       | new relationships        | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", "B"), ("C", "B")] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["B"]      | ["D"]             | ["A", "D", "C"] | [("A", "D"), ("C", "D")] | ["A", "C"]      | ["D"]            |


    Scenario Outline: Removing Relationships
        Given an empty graph
        When adding tasks <tasks>
        And adding relationships <relationships>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain relationships <relationships>
        And the tasks <finished before> should be finished
        And the tasks <unfinished before> should be unfinished
        When removing relationships <removed>
        Then the graph should contain tasks <new tasks>
        And the graph should contain relationships <new relationships>
        And the tasks <finished after> should be finished
        And the tasks <unfinished after> should be unfinished

        Examples: Fan-Out
            | tasks           | relationships            | update tasks    | finished before | unfinished before | removed      | new tasks       | new relationships        | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", "B"), ("A", "C")] | ["A", "B", "C"] | ["A", "B", "C"] | []                | [("A", "B")] | ["A", "B", "C"] | [("A", "C")]             | []              | ["A", "B", "C"]  |

        Examples: Fan-In
            | tasks           | relationships            | update tasks    | finished before | unfinished before | removed      | new tasks       | new relationships        | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", "B"), ("C", "B")] | ["A", "B", "C"] | ["A", "B", "C"] | []                | [("A", "B")] | ["A", "B", "C"] | [("C", "B")]             | ["C"]           | ["A", "B"]       |


    Scenario Outline: Removing Tasks
        Given an empty graph
        When adding tasks <tasks>
        And adding relationships <relationships>
        And updating tasks <update tasks>
        Then the graph should contain tasks <tasks>
        And the graph should contain relationships <relationships>
        And the tasks <finished before> should be finished
        And the tasks <unfinished before> should be unfinished
        When removing tasks <removed>
        Then the graph should contain tasks <new tasks>
        And the graph should contain relationships <new relationships>
        And the tasks <finished after> should be finished
        And the tasks <unfinished after> should be unfinished

        Examples: Fan-Out
            | tasks           | relationships            | update tasks    | finished before | unfinished before | removed    | new tasks       | new relationships        | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", "B"), ("A", "C")] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["A"]      | ["B", "C"]      | []                       | []              | ["B", "C"]       |
            | ["A", "B", "C"] | [("A", "B"), ("A", "C")] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["B"]      | ["A", "C"]      | [("A", "C")]             | ["A", "C"]      | []               |

        Examples: Fan-In
            | tasks           | relationships            | update tasks    | finished before | unfinished before | removed    | new tasks       | new relationships        | finished after  | unfinished after |
            | ["A", "B", "C"] | [("A", "B"), ("C", "B")] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["A"]      | ["B", "C"]      | [("C", "B")]             | ["C"]           | ["B"]            |
            | ["A", "B", "C"] | [("A", "B"), ("C", "B")] | ["A", "B", "C"] | ["A", "B", "C"] | []                | ["B"]      | ["A", "C"]      | []                       | ["A", "C"]      | []               |


    Scenario Outline: Updating Tasks
        Given an empty graph
        When adding tasks <tasks>
        And adding relationships <relationships>
        Then the graph should contain tasks <tasks>
        And the graph should contain relationships <relationships>
        When updating tasks <update tasks>
        Then tasks <updated> are updated
        And tasks <executed> are executed
        And tasks <finished> are finished
        And the tasks <finished tasks> should be finished
        And the tasks <unfinished tasks> should be unfinished

        Examples: Fan-Out
            | tasks           | relationships            | update tasks | updated              | executed        | finished        | finished tasks  | unfinished tasks |
            | ["A", "B", "C"] | [("A", "B"), ("A", "C")] | []           | []                   | []              | []              | []              | ["A", "B", "C"]  |
            | ["A", "B", "C"] | [("A", "B"), ("A", "C")] | ["A"]        | ["A"]                | ["A"]           | ["A"]           | ["A"]           | ["B", "C"]       |
            | ["A", "B", "C"] | [("A", "B"), ("A", "C")] | ["A", "A"]   | ["A", "A"]           | ["A"]           | ["A"]           | ["A"]           | ["B", "C"]       |
            | ["A", "B", "C"] | [("A", "B"), ("A", "C")] | ["B"]        | ["A", "B"]           | ["A", "B"]      | ["A", "B"]      | ["A", "B"]      | ["C"]            |
            | ["A", "B", "C"] | [("A", "B"), ("A", "C")] | ["B", "C"]   | ["A", "B", "A", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | []               |

        Examples: Fan-In
            | tasks           | relationships            | update tasks | updated              | executed        | finished        | finished tasks  | unfinished tasks |
            | ["A", "B", "C"] | [("A", "C"), ("B", "C")] | []           | []                   | []              | []              | []              | ["A", "B", "C"]  |
            | ["A", "B", "C"] | [("A", "C"), ("B", "C")] | ["A"]        | ["A"]                | ["A"]           | ["A"]           | ["A"]           | ["B", "C"]       |
            | ["A", "B", "C"] | [("A", "C"), ("B", "C")] | ["C"]        | ["A", "B", "C"]      | ["A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | []               |
            | ["A", "B", "C"] | [("A", "C"), ("B", "C")] | ["C", "A"]   | ["A", "B", "C", "A"] | ["A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | []               |

        Examples: Cycles
            | tasks           | relationships                        | update tasks | updated                        | executed        | finished        | finished tasks  | unfinished tasks |
            | ["A", "B", "C"] | [("A", "B"), ("B", "C"), ("C", "A")] | []           | []                             | []              | []              | []              | ["A", "B", "C"]  |
            | ["A", "B", "C"] | [("A", "B"), ("B", "C"), ("C", "A")] | ["A"]        | ["B", "C", "A"]                | ["B", "C", "A"] | ["B", "C", "A"] | ["A", "B", "C"] | []               |
            | ["A", "B", "C"] | [("A", "B"), ("B", "C"), ("C", "A")] | ["B"]        | ["C", "A", "B"]                | ["C", "A", "B"] | ["C", "A", "B"] | ["A", "B", "C"] | []               |
            | ["A", "B", "C"] | [("A", "B"), ("B", "C"), ("C", "A")] | ["C"]        | ["A", "B", "C"]                | ["A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | []               |
            | ["A", "B", "C"] | [("A", "B"), ("B", "C"), ("C", "A")] | ["C", "C"]   | ["A", "B", "C", "A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | []               |
            | ["A", "B", "C"] | [("A", "B"), ("B", "C"), ("C", "A")] | ["C", "A"]   | ["A", "B", "C", "B", "C", "A"] | ["A", "B", "C"] | ["A", "B", "C"] | ["A", "B", "C"] | []               |


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
        And adding relationships [("A", "B"), ("B", "C")]
        And updating task "C"
        Then the tasks ["A"] should be finished
        And the tasks ["B", "C"] should be failed


    Scenario: Adding Duplicate Tasks
        Given an empty graph
        When adding tasks ["A", "B", "C"]
        And adding relationships [("A", "B"), ("B", "C")]
        And adding task "A" an exception should be raised
        Then tasks [] are updated
        And the graph should contain tasks ["A", "B", "C"]
        And the graph should contain relationships [("A", "B"), ("B", "C")]


    Scenario: Adding Relationship With Nonexistent Task
        Given an empty graph
        When adding tasks ["A", "B", "C"]
        And adding relationships [("A", "B"), ("B", "C")]
        And adding relationship ("A", "D") an exception should be raised
        Then tasks [] are updated
        And the graph should contain tasks ["A", "B", "C"]
        And the graph should contain relationships [("A", "B"), ("B", "C")]


    Scenario: Removing Nonexistent Relationship
        Given an empty graph
        When adding tasks ["A", "B", "C"]
        And adding relationships [("A", "B"), ("B", "C")]
        And removing relationship ("A", "C") an exception should be raised
        Then tasks [] are updated
        And the graph should contain tasks ["A", "B", "C"]
        And the graph should contain relationships [("A", "B"), ("B", "C")]


    Scenario: Changing Task Functions
        Given an empty graph
        When adding tasks ["A", "B", "C"] with functions [graphcat.constant(1), graphcat.constant(2), graphcat.constant(3)]
        And adding relationships [("A", "B"), ("B", "C")]
        And updating tasks ["A", "B", "C"]
        Then the tasks ["A", "B", "C"] should be finished
        And the task ["A", "B", "C"] outputs should be [1, 2, 3]
        When the task "B" function is changed to None
        Then the tasks ["A"] should be finished
        And the tasks ["B", "C"] should be unfinished
        And the task ["A", "B", "C"] outputs should be [1, None, 3]


    Scenario: Expression Tasks
        Given an empty graph
        When adding tasks ["A", "B"] with functions [graphcat.constant(1), graphcat.constant(2)]
        And adding an expression task "C" with expression "3+4"
        And updating tasks ["A", "B", "C"]
        Then the graph should contain tasks ["A", "B", "C"]
        And the graph should contain relationships []
        And the tasks ["A", "B", "C"] should be finished
        And the task ["A", "B", "C"] outputs should be [1, 2, 7]
        When changing the expression task "C" to expression "out('A') + 1.1"
        Then the graph should contain relationships [("A", "C")]
        And the tasks ["A", "B", "C"] should be finished
        And the task ["A", "B", "C"] outputs should be [1, 2, 2.1]
        When the task "A" function is changed to graphcat.constant(3)
        Then the task ["A", "B", "C"] outputs should be [3, 2, 4.1]
        When changing the expression task "C" to expression "out('B') + 1.1"
        Then the graph should contain relationships [("B", "C")]
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
        And adding relationships [("A", "B"), ("A", "C"), ("B", "D")]
        And updating tasks ["D"]
        Then displaying the graph in a notebook should produce a visualization


    Scenario: Named Inputs
        Given an empty graph
        When adding tasks ["A", "B", "C"] with functions [graphcat.constant(2), graphcat.constant(3), None]
        And adding relationships [("A", "C"), ("B", "C")] to inputs ["lhs", "rhs"]
        And updating tasks ["C"]
        Then tasks ["A", "B", "C"] are executed with inputs [{}, {}, {"lhs": [2], "rhs": [3]}]
        When setting relationship [("B", "C")] inputs to [None]
        Then the tasks ["A", "B"] should be finished
        And the tasks ["C"] should be unfinished
        When updating tasks ["C"]
        Then tasks ["C"] are executed with inputs [{"lhs": [2], None: [3]}]



