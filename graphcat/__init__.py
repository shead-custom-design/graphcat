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

"""Functionality for managing and executing computational graphs.
"""

__version__ = "1.0.5"

import logging

log = logging.getLogger(__name__)

from graphcat.common import *
from graphcat.dynamic import DynamicGraph
from graphcat.static import StaticGraph
from graphcat.streaming import StreamingGraph

