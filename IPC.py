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
import logging
import multiprocessing as mp
from multiprocessing import managers
from typing import Callable, Dict, Tuple

import Def
import Logging

Manager: managers.SyncManager


########
# States

class State:
    local_name: str = None

    Camera: mp.Value = None
    Controller: mp.Value = None
    Display: mp.Value = None
    Gui: mp.Value = None
    Io: mp.Value = None
    Logger: mp.Value = None
    Worker: mp.Value = None


def set_state(new_state: int):
    """Set state of local process to new_state"""
    getattr(State, State.local_name).value = new_state


def get_state(process_name: str = None):
    """Get state of process.

    By default, if process_name is None, the local process's name is used
    """
    if process_name is None:
        process_name = State.local_name

    return getattr(State, process_name).value


def in_state(state: int, process_name: str = None):
    """Check if process is in the given state.

    By default, if process_name is None, the local process's name is used
    """
    if process_name is None:
        process_name = State.local_name

    return get_state(process_name) == state


########
# Pipes
# TODO: pipes have *limited buffer size*. This means if processes send
#  messages more quickly than the consumer can sort them out, this will crash
#  the producer process (can happen e.g. for very frequent event triggered signals)
#  ----
#  -> One solution may be an arbitrary limit on how often a pipe can be used to send
#  messages in a given time window. Although this would disregard the size of messages:
#  Another proposal which checks the buffer size against a maxsize:
#  https://stackoverflow.com/questions/45318798/how-to-detect-multiprocessing-pipe-is-full
#  Question: Overhead?

Pipes: Dict[str, Tuple[mp.connection.Connection]] = dict()


def send(process_name: str, signal: int, *args, **kwargs):
    """Send a message to another process via pipe.

    Convenience function for sending messages to process with process_name.
    All messages have the format [Signal code, Argument list, Keyword argument dictionary]

    @param process_name:
    @param signal:
    @param args:
    @param kwargs:

    """
    Logging.write(logging.DEBUG,
                  f'Send to process {process_name} with signal {signal} > args: {args} > kwargs: {kwargs}')
    Pipes[process_name][0].send([signal, args, kwargs])

def rpc(process_name: str, function: Callable, *args, **kwargs):
    """Send a remote procedure call of given function to another process.

    @param process_name:
    @param function:
    @param args:
    @param kwargs:
    """
    send(process_name, Def.Signal.rpc, function.__qualname__, *args, **kwargs)


########
# Buffer objects

class Routines:
    # Routine names *MUST* be identical to the corresponding process names in 'Def.Process'
    # e.g. Def.Process.Camera = 'Camera' -> Routines.Camera
    Camera = None
    Display = None
    Io = None

class Log:
    File = None
    Queue = None
    History = None

########
# Controls

class Control:
    General = None
    Recording = None
    Protocol = None
