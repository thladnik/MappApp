"""
MappApp ./process/Core.py - Process which handles rendering of visual visuals.
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

from vispy import app
from vispy import gloo
import time

import Config
import Def
import IPC
import process
import Protocol
import protocols
from visuals import AbstractVisual

if Def.Env == Def.EnvTypes.Dev:
    pass

app.use_app('PyQt5')
gloo.gl.use_gl('gl2')

class Canvas(app.Canvas):

    def __init__(self, _interval, *args, **kwargs):
        app.Canvas.__init__(self, *args, **kwargs)
        self.tick = 0
        self.measure_fps(0.1, self.show_fps)
        self.visual = None
        gloo.set_viewport(0, 0, *self.physical_size)
        gloo.set_clear_color((0.0, 0.0, 0.0, 1.0))

        self._timer = app.Timer(_interval, connect=self.on_timer, start=True)

        #self.native.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.t = time.perf_counter()
        self.show()

    def on_draw(self, event):
        pass

    def on_timer(self, event):

        gloo.clear()

        if self.visual is not None:
            # Leave catch in here for now.
            # This makes debugging new stimuli much easier.
            try:

                #print(time.time()-self.t)
                self.t = time.time()
                self.visual.draw(time.perf_counter())
            except Exception as exc:
                import traceback
                print(traceback.print_exc())

        self.update()

    def show_fps(self, fps):
        pass
        #print("FPS {:.2f}".format(fps))

    def on_resize(self, event):
        gloo.set_viewport(0, 0, *event.physical_size)


class Display(process.AbstractProcess):
    name = Def.Process.Display

    protocol: Protocol.AbstractProtocol = None
    visual: AbstractVisual = None

    def __init__(self, **kwargs):
        process.AbstractProcess.__init__(self, **kwargs)

        # Create canvas
        _interval = 1./Config.Display[Def.DisplayCfg.fps]
        _size = (Config.Display[Def.DisplayCfg.window_width],
                 Config.Display[Def.DisplayCfg.window_height])
        _position = (Config.Display[Def.DisplayCfg.window_pos_x],
                     Config.Display[Def.DisplayCfg.window_pos_y])
        self.canvas = Canvas(_interval,
                             size=_size,
                             resizable=False,
                             position=_position,
                             always_on_top=True)
        self.canvas.fullscreen = Config.Display[Def.DisplayCfg.window_fullscreen]

        # Run event loop
        self.run(1/200)

    def _prepare_protocol(self):
        self.protocol = protocols.load(IPC.Control.Protocol[Def.ProtocolCtrl.name])(self.canvas)
        try:
            self.protocol.initialize()
        except Exception as exc:
            import traceback
            print(traceback.print_exc())

    def _prepare_phase(self):
        phase_id = IPC.Control.Protocol[Def.ProtocolCtrl.phase_id]
        self.visual = self.protocol.fetch_phase_visual(phase_id)
        self.canvas.visual = self.visual
        IPC.Routines.Display.set_record_group(f'phase_{phase_id}',
                                              group_attributes=self.visual.parameters)

    def _cleanup_protocol(self):
        self.visual = None
        self.canvas.visual = self.visual

    def _start_shutdown(self):
        process.AbstractProcess._start_shutdown(self)

    def main(self):
        app.process_events()

        try:
            if self._run_protocol():
                IPC.Routines.Display.update(self.visual)
            else:
                IPC.Routines.Display.update()
        except Exception as exc:
            import traceback
            traceback.print_exc()
