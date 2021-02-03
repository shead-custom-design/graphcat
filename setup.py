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

from setuptools import setup, find_packages
import re

setup(
    name="graphcat",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    description="Lightweight, flexible toolkit for managing computational graphs.",
    install_requires=[
        "blinker",
        "networkx",
    ],
    long_description="""Graphcat provides a lightweight, flexible toolkit for managing computational graphs.
    See the Graphcat documentation at http://graphcat.readthedocs.io, and the Graphcat sources at http://github.com/shead-custom-design/graphcat""",
    maintainer="Timothy M. Shead",
    maintainer_email="tim@shead-custom-design.com",
    packages=find_packages(),
    project_urls={
        "Chat": "https://graphcat.zulipchat.com",
        "Coverage": "https://coveralls.io/r/shead-custom-design/graphcat",
        "Documentation": "https://graphcat.readthedocs.io",
        "Issue Tracker": "https://github.com/shead-custom-design/graphcat/issues",
        "Regression Tests": "https://travis-ci.org/shead-custom-design/graphcat",
        "Source": "https://github.com/shead-custom-design/graphcat",
    },
    scripts=[
    ],
    url="https://graphcat.readthedocs.io",
    version=re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]",
        open(
            "graphcat/__init__.py",
            "r").read(),
        re.M).group(1),
)
