"""
MappApp ./Controller.py - Controller process class.
Controller spawns all sub processes.
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
import logging
import multiprocessing as mp
import os
import time
from typing import List, Dict, Tuple

import routines
import Config
import Def
from helper import Basic
import IPC
import Logging
import process
import protocols

class Controller(process.AbstractProcess):
    name = Def.Process.Controller

    configfile: str = None

    _processes: Dict[str, mp.Process] = dict()
    _registered_processes: List[Tuple[process.AbstractProcess, Dict]] = list()

    _protocol_processes: List[str] = [Def.Process.Camera, Def.Process.Display, Def.Process.Io, Def.Process.Worker]
    _active_protocols: List[str] = list()

    def __init__(self):
        # Set up manager
        IPC.Manager = mp.Manager()

        # Set up logging
        IPC.Log.Queue = mp.Queue()
        IPC.Log.History = IPC.Manager.list()
        IPC.Log.File = IPC.Manager.Value(ctypes.c_char_p, '')

        # Set file to log to
        if IPC.Log.File.value == '':
            IPC.Log.File.value = '{}.log'.format(time.strftime('%Y-%m-%d-%H-%M-%S'))

        # Set up logger, formatte and handler
        self.logger = logging.getLogger('mylog')
        h = logging.handlers.TimedRotatingFileHandler(
            os.path.join(Def.Path.Log, IPC.Log.File.value), 
            'd')
        h.setFormatter(logging.Formatter(
            '%(asctime)s <<>> %(name)-10s <<>> %(levelname)-8s <<>> %(message)s <<'))
        self.logger.addHandler(h)

        # Initialize AbstractProcess
        process.AbstractProcess.__init__(self, _log={k: v for k, v in IPC.Log.__dict__.items()
                                             if not (k.startswith('_'))})
        # Manually set up pipe for controller
        IPC.Pipes[self.name] = mp.Pipe()

        # Set configurations
        try:
            Logging.write(Logging.INFO,
                          'Using configuration from file {}'.format(self.configfile))
            self.configuration = Basic.ConfigParser()
            self.configuration.read(self.configfile)
            # Camera
            Config.Camera = IPC.Manager.dict()
            Config.Camera.update(self.configuration.getParsedSection(Def.CameraCfg.name))
            # Display
            Config.Display = IPC.Manager.dict()
            Config.Display.update(self.configuration.getParsedSection(Def.DisplayCfg.name))
            # Gui
            Config.Gui = IPC.Manager.dict()
            Config.Gui.update(self.configuration.getParsedSection(Def.GuiCfg.name))
            # IO
            Config.Io = IPC.Manager.dict()
            Config.Io.update(self.configuration.getParsedSection(Def.IoCfg.name))
            # Recording
            Config.Recording = IPC.Manager.dict()
            Config.Recording.update(self.configuration.getParsedSection(Def.RecCfg.name))
        except Exception:
            print('Loading of configuration file {} failed.'.format(self.configfile))
            import traceback
            traceback.print_exc()

        # TODO: check if recording routines contains any entries
        #  for inactive processes or inactive routines on active processes
        #  print warning or just shut down completely in-case?

        ################################
        # Set up STATES

        IPC.State.Controller = IPC.Manager.Value(ctypes.c_int8, Def.State.NA)
        IPC.State.Camera = IPC.Manager.Value(ctypes.c_int8, Def.State.NA)
        IPC.State.Display = IPC.Manager.Value(ctypes.c_int8, Def.State.NA)
        IPC.State.Gui = IPC.Manager.Value(ctypes.c_int8, Def.State.NA)
        IPC.State.Io = IPC.Manager.Value(ctypes.c_int8, Def.State.NA)
        IPC.State.Worker = IPC.Manager.Value(ctypes.c_int8, Def.State.NA)

        ################################
        # Set up CONTROLS

        # General
        IPC.Control.General = IPC.Manager.dict()
        # Set avg. minimum sleep period
        times = list()
        for i in range(100):
            t = time.perf_counter()
            time.sleep(10**-10)
            times.append(time.perf_counter()-t)
        IPC.Control.General.update({Def.GenCtrl.min_sleep_time : max(times)})
        Logging.write(Logging.INFO, 'Minimum sleep period is {0:.3f}ms'.format(1000*max(times)))
        IPC.Control.General.update({Def.GenCtrl.process_null_time: time.time() + 100.})

        # Check time precision on system
        dt = list()
        t0 = time.time()
        while len(dt) < 100:
            t1 = time.time()
            if t1 > t0:
                dt.append(t1-t0)
        avg_dt = sum(dt) / len(dt)
        msg = 'Timing precision on system {0:3f}ms'.format(1000*avg_dt)
        if avg_dt > 0.001:
            msg_type = Logging.WARNING
        else:
            msg_type = Logging.INFO
        Logging.write(msg_type, msg)

        # Recording
        IPC.Control.Recording = IPC.Manager.dict()
        IPC.Control.Recording.update({Def.RecCtrl.active: False,
                                      Def.RecCtrl.folder: ''})

        # Protocol
        IPC.Control.Protocol = IPC.Manager.dict({Def.ProtocolCtrl.name: None,
                                                 Def.ProtocolCtrl.phase_id: None,
                                                 Def.ProtocolCtrl.phase_start: None,
                                                 Def.ProtocolCtrl.phase_stop: None})

        # Set up routines
        # Camera
        IPC.Routines.Camera = routines.Routines(
            Def.Process.Camera,
            routines=Config.Camera[Def.CameraCfg.routines] if Config.Camera[Def.CameraCfg.use] else None
        )

        # Display
        IPC.Routines.Display = routines.Routines(
            Def.Process.Display,
            routines=Config.Display[Def.DisplayCfg.routines] if Config.Display[Def.DisplayCfg.use] else None
        )

        # IO
        IPC.Routines.Io = routines.Routines(
            Def.Process.Io,
            routines=Config.Io[Def.IoCfg.routines] if Config.Io[Def.IoCfg.use] else None
        )

        # Set up processes
        # Worker
        self._register_process(process.Worker)
        # GUI
        if Config.Gui[Def.GuiCfg.use]:
            self._register_process(process.Gui)
        # Camera
        if Config.Camera[Def.CameraCfg.use]:
            self._register_process(process.Camera)
        # Display
        if Config.Display[Def.DisplayCfg.use]:
            self._register_process(process.Display)
        # IO
        if Config.Io[Def.IoCfg.use]:
            self._register_process(process.Io)

        # Select subset of registered processes which should implement
        # the _run_protocol method
        self._active_protocols = list(set([p[0].__name__ for p in self._registered_processes])
                                      & set(self._protocol_processes))
        Logging.write(Logging.INFO,
                      'Protocolled processes: {}'.format(str(self._active_protocols)))

        # Set up protocol
        self.current_protocol = None

        # Run event loop
        self.start()

    def _register_process(self, target, **kwargs):
        """Register new process to be spawned.

        :param target: process class
        :param kwargs: optional keyword arguments for initalization of process class
        """
        self._registered_processes.append((target, kwargs))

    def initialize_process(self, target, **kwargs):

        process_name = target.name

        if process_name in self._processes:
            # Terminate process
            Logging.write(Logging.INFO, 'Restart process {}'.format(process_name))
            self._processes[process_name].terminate()

            # Set process state
            # (this is the ONLY instance where a process state may be set externally)
            getattr(IPC.State, process_name).value = Def.State.STOPPED

            # Delete references
            del self._processes[process_name]

        # Update keyword args
        kwargs.update(dict(
                          _pipes=IPC.Pipes,
                          _configurations={k: v for k, v
                                           in Config.__dict__.items()
                                           if not (k.startswith('_'))},
                          _states={k: v for k, v
                                   in IPC.State.__dict__.items()
                                   if not (k.startswith('_'))},
                          _routines={k: v for k, v
                                     in IPC.Routines.__dict__.items()
                                     if not (k.startswith('_'))},
                          _controls={k: v for k, v
                                     in IPC.Control.__dict__.items()
                                     if not (k.startswith('_'))},
                          _log={k: v for k, v
                                in IPC.Log.__dict__.items()
                                if not (k.startswith('_'))}
                      ))

        # Create subprocess
        self._processes[process_name] = mp.Process(target=target,
                                                  name=process_name,
                                                  kwargs=kwargs)

        # Start subprocess
        self._processes[process_name].start()

        # Set state to IDLE
        self.set_state(Def.State.IDLE)

    def start(self):
        # Initialize all pipes
        for target, kwargs in self._registered_processes:
            IPC.Pipes[target.name] = mp.Pipe()

        # Initialize all processes
        for target, kwargs in self._registered_processes:
            self.initialize_process(target, **kwargs)

        # Run controller
        self.run(interval=0.001)

        # Shutdown procedure
        Logging.write(Logging.DEBUG, 'Wait for processes to terminate')
        while True:
            # Complete shutdown if all processes are deleted
            if not(bool(self._processes)):
                break

            # Check status of processes until last one is stopped
            for process_name in list(self._processes):
                if not(getattr(IPC.State, process_name).value == Def.State.STOPPED):
                    continue

                # Terminate and delete references
                self._processes[process_name].terminate()
                del self._processes[process_name]
                del IPC.Pipes[process_name]

        self._running = False
        self.set_state(Def.State.STOPPED)

    ################
    # Recording

    def toggle_enable_recording(self, newstate):
        Config.Recording[Def.RecCfg.enabled] = newstate

    def start_recording(self, compression_method=None, compression_opts=None):
        if IPC.Control.Recording[Def.RecCtrl.active]:
            Logging.write(Logging.WARNING, 'Tried to start new recording while active')
            return False

        # Set current folder if none is given
        if not(bool(IPC.Control.Recording[Def.RecCtrl.folder])):
            IPC.Control.Recording[Def.RecCtrl.folder] = 'rec_{}'.format(time.strftime('%Y-%m-%d-%H-%M-%S'))

        # Create output folder
        out_path = os.path.join(Config.Recording[Def.RecCfg.output_folder], IPC.Control.Recording[Def.RecCtrl.folder])
        Logging.write(Logging.DEBUG, 'Set output folder {}'.format(out_path))
        if not(os.path.exists(out_path)):
            Logging.write(Logging.DEBUG, 'Create output folder {}'.format(out_path))
            os.mkdir(out_path)

        IPC.Control.Recording[Def.RecCtrl.use_compression] = compression_method is not None
        IPC.Control.Recording[Def.RecCtrl.compression_method] = compression_method
        IPC.Control.Recording[Def.RecCtrl.compression_opts] = compression_opts

        # Set state to recording
        Logging.write(Logging.INFO, 'Start recording')
        IPC.Control.Recording[Def.RecCtrl.active] = True

        return True

    def pause_recording(self):
        if not(IPC.Control.Recording[Def.RecCtrl.active]):
            Logging.write(Logging.WARNING, 'Tried to pause inactive recording.')
            return

        Logging.write(Logging.INFO, 'Pause recording')
        IPC.Control.Recording[Def.RecCtrl.active] = False

    def stop_recording(self, sessiondata=None):
        if IPC.Control.Recording[Def.RecCtrl.active]:
            IPC.Control.Recording[Def.RecCtrl.active] = False

        if not(Config.Gui[Def.GuiCfg.use]) and sessiondata is None:
            # TODO: prompt user for sessiondata?
            pass


        # Save metadata and externally provided sessiondata
        metadata = dict(hello1name='test', hello2val=123)
        #TODO: compose proper metadata, append sessiondata and save to file

        # Let worker compose all individual recordings into one data structure
        if False:
            IPC.rpc(Def.Process.Worker, process.Worker.run_task,
                     'ComposeRecordings',
                    IPC.Control.Recording[Def.RecCtrl.folder])

        Logging.write(Logging.INFO, 'Stop recording')
        self.set_state(Def.State.IDLE)
        IPC.Control.Recording[Def.RecCtrl.folder] = ''


    def start_protocol(self, protocol_path):
        # TODO: also make this dynamic
        # If any relevant subprocesses are currently busy: abort
        if not(self.in_state(Def.State.IDLE, Def.Process.Display)):
            processes = list()
            if not(self.in_state(Def.State.IDLE, Def.Process.Display)):
                processes.append(Def.Process.Display)
            if not (self.in_state(Def.State.IDLE, Def.Process.Io)):
                processes.append(Def.Process.Io)

            Logging.write(Logging.WARNING,
                          'One or more processes currently busy. Can not start new protocol.'
                          '(Processes: {})'.format(','.join(processes)))
            return

        # Start recording if enabled; abort if recording can't be started
        if Config.Recording[Def.RecCfg.enabled] \
                and not(IPC.Control.Recording[Def.RecCtrl.active]):
            if not(self.start_recording()):
                return

        # Set phase info
        IPC.Control.Protocol[Def.ProtocolCtrl.phase_id] = None
        IPC.Control.Protocol[Def.ProtocolCtrl.phase_start] = None
        IPC.Control.Protocol[Def.ProtocolCtrl.phase_stop] = None
        # Set protocol class path
        IPC.Control.Protocol[Def.ProtocolCtrl.name] = protocol_path

        # Go into PREPARE_PROTOCOL
        self.set_state(Def.State.PREPARE_PROTOCOL)

    def start_protocol_phase(self, _id = None):
        # If phase ID was provided: run thcontrolsis ID
        if not(_id is None):
            IPC.Control.Protocol[Def.ProtocolCtrl.phase_id] = _id
            return

        # Else: advance protocol counter
        if IPC.Control.Protocol[Def.ProtocolCtrl.phase_id] is None:
            IPC.Control.Protocol[Def.ProtocolCtrl.phase_id] = 0
        else:
            IPC.Control.Protocol[Def.ProtocolCtrl.phase_id] = IPC.Control.Protocol[Def.ProtocolCtrl.phase_id] + 1

    def abortProtocol(self):
        # TODO: handle stuff?
        IPC.Control.Protocol[Def.ProtocolCtrl.phase_stop] = time.time()
        self.set_state(Def.State.PROTOCOL_END)

    def main(self):

        ########
        # First: handle logging
        while not(IPC.Log.Queue.empty()):

            # Fetch next record
            record = IPC.Log.Queue.get()

            try:
                self.logger.handle(record)
                IPC.Log.History.append(dict(levelno=record.levelno,
                                            asctime=record.asctime,
                                            name=record.name,
                                            levelname=record.levelname,
                                            msg=record.msg))
            except Exception:
                import sys, traceback
                print('Exception in Logger:', file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

        ########
        # PREPARE_PROTOCOL
        if self.in_state(Def.State.PREPARE_PROTOCOL):

            self.protocol = protocols.load(IPC.Control.Protocol[Def.ProtocolCtrl.name])(self)

            # Wait for processes to WAIT_FOR_PHASE (if they are not stopped)
            check = [not(IPC.in_state(Def.State.WAIT_FOR_PHASE, process_name))
                     for process_name in self._active_protocols]
            if any(check):
                return

            # Set next phase
            self.start_protocol_phase()

            # Set PREPARE_PHASE
            self.set_state(Def.State.PREPARE_PHASE)

        ########
        # PREPARE_PHASE
        if self.in_state(Def.State.PREPARE_PHASE):

            # Wait for processes to be ready (have phase prepared)
            check = [not(IPC.in_state(Def.State.READY, process_name))
                     for process_name in self._active_protocols]
            if any(check):
                return

            # Start phase
            phase_id = IPC.Control.Protocol[Def.ProtocolCtrl.phase_id]
            duration = self.protocol.fetch_phase_duration(phase_id)

            fixed_delay = 0.1
            IPC.Control.Protocol[Def.ProtocolCtrl.phase_start] = time.time() + fixed_delay
            IPC.Control.Protocol[Def.ProtocolCtrl.phase_stop] = time.time() + duration + fixed_delay

            Logging.write(Logging.INFO,
                          'Run phase {}. Set start time to {}'
                          .format(IPC.Control.Protocol[Def.ProtocolCtrl.phase_id],
                                  IPC.Control.Protocol[Def.ProtocolCtrl.phase_start]))

            # Set to running
            self.set_state(Def.State.RUNNING)

        ########
        # RUNNING
        elif self.in_state(Def.State.RUNNING):

            # If stop time is reached, set PHASE_END
            if IPC.Control.Protocol[Def.ProtocolCtrl.phase_stop] < time.time():
                Logging.write(Logging.INFO,
                              'End phase {}.'
                              .format(IPC.Control.Protocol[Def.ProtocolCtrl.phase_id]))

                self.set_state(Def.State.PHASE_END)

                return

        ########
        # PHASE_END
        elif self.in_state(Def.State.PHASE_END):

            # If there are no further phases, end protocol
            phase_id = IPC.Control.Protocol[Def.ProtocolCtrl.phase_id]
            if (phase_id + 1) >= self.protocol.phase_count():
                self.set_state(Def.State.PROTOCOL_END)
                return

            # Else, continue with next phase
            self.start_protocol_phase()

            # Move to PREPARE_PHASE (again)
            self.set_state(Def.State.PREPARE_PHASE)

        ########
        # PROTOCOL_END
        elif self.in_state(Def.State.PROTOCOL_END):

            # When all processes are in IDLE again, stop recording and
            # move Controller to IDLE
            check = [IPC.in_state(Def.State.IDLE, process_name)
                     for process_name in self._active_protocols]
            if all(check):

                self.stop_recording()

                IPC.Control.Protocol[Def.ProtocolCtrl.name] = ''

                self.set_state(Def.State.IDLE)

        else:
            # If nothing's happning: sleep for a bit
            time.sleep(0.05)

    def _start_shutdown(self):
        Logging.write(Logging.DEBUG, 'Shut down processes')
        self._shutdown = True
        for process_name in self._processes:
            IPC.send(process_name, Def.Signal.shutdown)