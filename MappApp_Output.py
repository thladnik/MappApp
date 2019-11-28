from glumpy import app, gl, glm
import numpy as np
import pyqtgraph.opengl as pyqtgl

import MappApp_Communication as macom
import MappApp_Definition as madef
from devices import Arduino

from IPython import embed

# Set Glumpy to use qt5 backend
app.use('qt5')

class Display:

    def __init__(self):

        ## Load client connections
        ipc = macom.IPC()
        ipc.loadConnections()
        self.clientToCtrl = ipc.getClientConnection(madef.Processes.CONTROL, madef.Processes.DISPLAY)

        ## Setup window
        self.window = app.Window(width=800, height=600, color=(1, 1, 1, 1))

        self.protocol = None

        # Apply event wrapper
        self.on_draw = self.window.event(self.on_draw)
        self.on_resize = self.window.event(self.on_resize)
        self.on_init = self.window.event(self.on_init)

        # Wait to receive display settings
        obj = self.clientToCtrl.recv()
        if not(obj[0] == macom.Display.Code.NewDisplaySettings):
            print('ERROR: display requires initial message to be the display configuration.')
            self.window.close()
        self.displaySettings = obj[1]

        # Check fullscreen state and change if necessary
        self.checkFullscreen()

    def startNewProtocol(self, protocol_cls, *args, **kwargs):

        ## Initialize new stimulus
        self.protocol = protocol_cls(*args, **kwargs)

        ## Attach viewport
        self.window.attach(self.protocol.program['viewport'])

    def _handleCommunication(self, dt):

        # Receive data
        if not(self.clientToCtrl.poll(timeout=.0001)):
            return

        ## Receive message
        obj = self.clientToCtrl.recv()

        ## App close event
        if obj[0] == macom.Display.Code.Close:
            print('Closing display')
            self.window.close()

        ## New display settings
        elif obj[0] == macom.Display.Code.NewDisplaySettings:

            # Update display settings
            self.displaySettings = obj[1]

            # Check fullscreen state and change if necessary
            self.checkFullscreen()

            # Dispatch resize event
            self.window.dispatch_event('on_resize', self.window.width, self.window.height)

        ## Start new stimulation protocol
        elif obj[0] == macom.Display.Code.SetNewStimulationProtocol:
            protocol = obj[1]

            args = []
            kwargs = dict()
            if len(obj) > 2:
                args = obj[2]
            if len(obj) > 3:
                kwargs = obj[3]

            # Setup new program
            self.startNewProtocol(protocol, *args, **kwargs)

            # Dispatch resize event
            self.window.dispatch_event('on_resize', self.window.width, self.window.height)

        ## New stimulus parameters
        elif obj[0] == macom.Display.Code.UpdateStimulusParams:
            stim = obj[1]
            if not(isinstance(self.protocol, stim)):
                print('WARNING: trying to update wrong stimulus type!')
                return

            kwargs = dict()
            if len(obj) > 2:
                kwargs = obj[2]

            self.protocol.update(**kwargs)

    def checkFullscreen(self):
        if self.window.get_fullscreen() != self.displaySettings[madef.DisplaySettings.bool_disp_fullscreen]:
            self.window.set_fullscreen(self.displaySettings[madef.DisplaySettings.bool_disp_fullscreen],
                                       screen=self.displaySettings[madef.DisplaySettings.int_disp_screen_id])

    def on_draw(self, dt):
        ## Only draw a frame if stimulus is set
        if self.protocol is None:
            return

        ## Clear window
        self.window.clear(color=(0.0, 0.0, 0.0, 1.0))  # black

        self.protocol.draw(dt)


    def on_resize(self, width, height):
        if self.protocol is None:
            return

        ## Update viewport (center local viewport with aspect = 1)
        if height > width:
            length = width
            x_offset = 0
            y_offset = (height - length) // 2
        else:
            length = height
            x_offset = (width - length) // 2
            y_offset = 0
        self.protocol.program['viewport']['global'] = (0, 0, width, height)
        self.protocol.program['viewport']['local'] = (x_offset, y_offset, length, length)

        # Draw
        self.window.dispatch_event('on_draw', 0.0)

    def update(self):

        ## Set default image channel parameters
        std_trans_distance = -10.
        std_fov = 30.
        std_elevation_rot = 90.
        std_radial_offset = 0.5
        std_tangent_offset = 0.

        elevation_rot_sw = 0.
        elevation_rot_se = 0.
        elevation_rot_ne = 0.
        elevation_rot_nw = 0.

        azimuth_rot_sw = 0.
        azimuth_rot_se = 0.
        azimuth_rot_ne = 0.
        azimuth_rot_nw = 0.

        ## SOUTH WEST
        # Non-linear transformations
        rot_axis_sw = (-1, 1, 0)
        u_projection = glm.perspective(std_fov, 1.0, 0.01, 1000.0)
        u_rot = np.eye(4, dtype=np.float32)
        glm.rotate(u_rot, azimuth_rot_sw, 0, 0, 1)  # Rotate around equator
        glm.rotate(u_rot, std_elevation_rot - elevation_rot_sw,
                   *rot_axis_sw)  # Rotate around current azim. major circle
        u_trans = glm.translation(0., 0., std_trans_distance)
        self.protocol.program['u_trans_sw'] = u_trans
        self.protocol.program['u_rot_sw'] = u_rot
        self.protocol.program['u_projection_sw'] = u_projection
        # Linear image plane transformations
        self.protocol.program['u_radial_offset_sw'] = std_radial_offset
        self.protocol.program['u_tangent_offset_sw'] = std_tangent_offset

        ## SOUTH EAST
        # Non-linear transformations
        rot_axis_se = (-1, -1, 0)
        u_projection = glm.perspective(std_fov, 1.0, 0.01, 1000.0)
        u_rot = np.eye(4, dtype=np.float32)
        glm.rotate(u_rot, azimuth_rot_se, 0, 0, 1)  # Rotate around equator
        glm.rotate(u_rot, std_elevation_rot - elevation_rot_se,
                   *rot_axis_se)  # Rotate around current azim. major circle
        u_trans = glm.translation(0., 0., std_trans_distance)
        self.protocol.program['u_trans_se'] = u_trans
        self.protocol.program['u_rot_se'] = u_rot
        self.protocol.program['u_projection_se'] = u_projection
        # Linear image plane transformations
        self.protocol.program['u_radial_offset_se'] = std_radial_offset
        self.protocol.program['u_tangent_offset_se'] = std_tangent_offset

        rot_axis_ne = (1, -1, 0)
        u_projection = glm.perspective(std_fov, 1.0, 0.01, 1000.0)
        u_rot = np.eye(4, dtype=np.float32)
        glm.rotate(u_rot, azimuth_rot_ne, 0, 0, 1)  # Rotate around equator
        glm.rotate(u_rot, std_elevation_rot - elevation_rot_ne,
                   *rot_axis_ne)  # Rotate around current azim. major circle
        u_trans = glm.translation(0., 0., std_trans_distance)
        self.protocol.program['u_trans_ne'] = u_trans
        self.protocol.program['u_rot_ne'] = u_rot
        self.protocol.program['u_projection_ne'] = u_projection
        # Linear image plane transformations
        self.protocol.program['u_radial_offset_ne'] = std_radial_offset
        self.protocol.program['u_tangent_offset_ne'] = std_tangent_offset

        rot_axis_nw = (1, 1, 0)
        u_projection = glm.perspective(std_fov, 1.0, 0.01, 1000.0)
        u_rot = np.eye(4, dtype=np.float32)
        glm.rotate(u_rot, azimuth_rot_nw, 0, 0, 1)  # Rotate around equator
        glm.rotate(u_rot, std_elevation_rot - elevation_rot_nw,
                   *rot_axis_nw)  # Rotate around current azim. major circle
        u_trans = glm.translation(0., 0., std_trans_distance)
        self.protocol.program['u_trans_nw'] = u_trans
        self.protocol.program['u_rot_nw'] = u_rot
        self.protocol.program['u_projection_nw'] = u_projection
        # Linear image plane transformations
        self.protocol.program['u_radial_offset_nw'] = std_radial_offset
        self.protocol.program['u_tangent_offset_nw'] = std_tangent_offset

        # Draw
        self.window.dispatch_event('on_draw', 0.0)

    def on_init(self):
        pass

def runDisplay(fps, *args, **kwargs):

    display = Display(*args, **kwargs)

    # Schedule glumpy to check for new inputs (keep this as INfrequent as possible, rendering has priority)
    app.clock.schedule_interval(display._handleCommunication, 0.1)
    #
    app.run(framerate=fps)

class StimulusInspector:

    def __init__(self):
        pass


    def draw(self):
        print('test')

def runStimulusInspector():
    from PyQt5 import QtCore, QtWidgets

    # Setup app and window
    app = QtWidgets.QApplication([])
    w = pyqtgl.GLViewWidget()
    w.resize(QtCore.QSize(600, 600))
    w.show()
    w.setWindowTitle('Stimulus preview')
    w.setCameraPosition(distance=3, azimuth=0)

    stiminspect = StimulusInspector()

    # Set timer for frame update
    timer = QtCore.QTimer()
    timer.timeout.connect(stiminspect.draw)
    timer.start(0.05)

    # Start event loop
    QtWidgets.QApplication.instance().exec_()