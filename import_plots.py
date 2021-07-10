"""
A program to manage chia farms and maximize the used of space available to the farmer.
You can download the latest from https://github.com/aelfakih/Manage-Chia-Farm

Copyright 2021 Adonis Elfakih

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

try:
    from io import UnsupportedOperation as IOUnsupportedOperation
except ImportError:
    class IOUnsupportedOperation(Exception):
        """A dummy exception to take the place of Python 3's
        ``io.UnsupportedOperation`` in Python 2"""

import pathlib
import os
import re
import sys
import shutil
import yaml
from database import *
from helpers import *
import collections
from PyInquirer import style_from_dict, Token, prompt, Separator
import logging


style = get_pyinquirer_style ( )
do_import_plots(style)