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

"""Functionality for testing preconditions and assertions.
"""

import functools
import sys


def loaded_module(modules):
    """Function decorator that tests whether module(s) have already been loaded.

    Parameters
    ----------
    modules: :class:`str` or sequence of :class:`str`, required
        Names of the modules that must already be loaded for the wrapped
        function to execute.

    Raises
    ------
    :class:`RuntimeError`
        If any module in `modules` isn't already loaded.
    """
    if isinstance(modules, str):
        modules = (modules,) # pragma: no cover
    def implementation(f):
        @functools.wraps(f)
        def implementation(*args, **kwargs):
            for module in modules:
                if module not in sys.modules:
                    raise RuntimeError(f"Module {module} could not be found.") # pragma: no cover
            return f(*args, **kwargs)
        return implementation
    return implementation

