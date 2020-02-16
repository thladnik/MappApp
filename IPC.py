"""
MappApp ./IPC.py - Inter-process-communication placeholders and functions.
all stimulus implementations in ./stimulus/.
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

import ctypes
from multiprocessing import managers

import Definition

Manager : managers.SyncManager

def createConfigDict():
    return Manager.dict()

def createSharedState():
    return Manager.Value(ctypes.c_int8, Definition.State.stopped)

class State:
    Camera     : int = None
    Controller : int = None
    Display    : int = None
    Gui        : int = None
    IO         : int = None
    Logger     : int = None
    Worker     : int = None

BufferObject = None