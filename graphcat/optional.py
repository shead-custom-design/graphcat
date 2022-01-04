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

"""Helpers for implementing optional functionality.
"""


def module(name):
    """Quietly load a module by name, ignoring errors.

    Note that dotted names, e.g. `pkg.mod` will return the
    top-level package, just like the `import` statement.

    Parameters
    ----------
    name: :class:`str`
        Name of the module to be loaded.

    Returns
    -------
    module: loaded module if successful, or :any:`None`.
    """
    try:
        return __import__(name, globals(), locals(), [], 0)
    except: # pragma: no cover
        pass
