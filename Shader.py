"""
MappApp ./Shader.py - Custom shader classes used in display process (./process/Core.py).
Copyright (C) 2020 Tim Hladnik

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import os

from Def import Path

class BasicFileShader:

    def __init__(self):
        self._flist = list()

    def addShaderFile(self, fname, subdir=None):
        if subdir is not None:
            fname = os.path.join(subdir, fname)
        self._flist.append(fname)

        return self

    def read(self):
        code = ''

        for fname in self._flist:
            with open(os.path.join(Path.Shader, fname), 'r') as fobj:
                code += fobj.read()
            code += '\n'

        return code
