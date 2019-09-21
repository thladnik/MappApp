from glumpy import app, gl, glm, gloo, transforms
import numpy as np
from multiprocessing import Pipe, Process
import time

from MappApp_Geometry import SphericalArena
import MappApp_Com as com


from IPython import embed

# Set Glumpy to use qt5 backend
app.use('qt5')

# Shaders
vertex = """
uniform mat4   u_model;         // Model matrix
uniform mat4   u_view;          // View matrix
uniform mat4   u_projection;    // Projection matrix
attribute vec3 a_position;      // Vertex position
attribute vec2 a_texcoord;      // Vertex texture coordinates
varying vec2   v_texcoord;      // Interpolated fragment texture coordinates (out)
void main()
{
    // Assign varying variables
    v_texcoord  = a_texcoord;
    // Final position
    gl_Position = u_projection * u_view * u_model * vec4(a_position,1.0);
    <viewport.transform>;
}
"""
fragment = """
uniform sampler2D u_texture;  // Texture 
varying vec2      v_texcoord; // Interpolated fragment texture coordinates (in)
void main()
{
    <viewport.clipping>;
    // Get texture color
    vec4 t_color = texture2D(u_texture, v_texcoord);
    // Final color
    gl_FragColor = t_color;
}
"""

# Define sphere
sphere = SphericalArena(theta_lvls=100, phi_lvls=50, upper_phi=45.0, radius=1.0)

class States:
    Idle = 0

    Terminated = 99

class Presenter:

    state = States.Idle

    def __init__(self, pipein, pipeout):
        self.pipein = pipein
        self.pipeout = pipeout

        self.disp_pipeout, self.disp_pipein = Pipe()

        self.display = Process(name='Display', target=runDisplay, args=(self.disp_pipein, self.disp_pipeout))
        self.display.start()

        # TODO: add second process which coordinates digital outputs

    def start(self):
        while self.state != States.Terminated:
            if self.pipeout.poll():
                obj = self.pipeout.recv()

                if obj[0] in range(*com.Display.ToPresenter.range):
                    if obj[0] == com.Display.ToPresenter.Close:
                        self.disp_pipein.send(com.Display.ToDisplay.Close)
                        # TODO: terminate process as soon as display window is closed
                        # TODO: report back that processes are terminated

                elif obj[0] in range(*com.Display.ToDisplay.range):
                    self.disp_pipein.send(obj)

                else:
                    print('WARNING: orphaned object in pipe.')


            #time.sleep(.001)

def runPresenter(*args, **kwargs):
    presenter = Presenter(*args, **kwargs)
    presenter.start()


class Display:

    modelRotationAxes = {
        'ne' : (1, -1, 0),
        'nw' : (1, 1, 0),
        'sw' : (-1, 1, 0),
        'se' : (-1, -1, 0)
    }

    modelZeroElevRotation =  {
        'ne' : -90.0,
        'nw' : -90.0,
        'sw' : -90.0,
        'se' : -90.0
    }

    modelElevRotation = {
        'ne' : 0.0,
        'nw' : 0.0,
        'sw' : 0.0,
        'se' : 0.0
    }

    def __init__(self, pipein, pipeout):
        self.pipein = pipein
        self.pipeout = pipeout

        self.window = app.Window(width=800, height=600, color=(1, 1, 1, 1))

        self.program = None
        self.stimulus = None
        self.vp_global_pos = (0., 0.)
        self.vp_global_size = 1.0
        self.disp_vp_center_dist = 0.0


        # Use event wrapper
        self.on_draw = self.window.event(self.on_draw)
        self.on_resize = self.window.event(self.on_resize)
        self.on_init = self.window.event(self.on_init)

        # Report ready
        self.pipeout.send([com.Display.ToMain.Ready])


    def setupProgram(self):
        self.program = dict()
        self.v = dict()
        self.i = dict()

        theta_range = 90.0
        for j, orient in enumerate(['ne', 'nw', 'sw', 'se']):
            theta_center = 45.0 + j * 90.0

            dir = sphere.sph2cart(theta_center, 0)

            thetas, phis = sphere.getThetaSubset(theta_center - theta_range / 2, theta_center + theta_range / 2)

            # Vertices
            vertices = sphere.sph2cart(thetas, phis)
            tex_coords = sphere.mercator2DTexture(thetas, phis)
            indices = sphere.getFaceIndices(vertices)
            self.v[orient] = np.zeros(vertices.shape[0],
                         [('a_position', np.float32, 3),
                          ('a_texcoord', np.float32, 2)])
            self.v[orient]['a_position'] = vertices.astype(np.float32)
            self.v[orient]['a_texcoord'] = tex_coords.astype(np.float32).T
            self.v[orient] = self.v[orient].view(gloo.VertexBuffer)

            # Indices
            self.i[orient] = indices.astype(np.uint32)
            self.i[orient] = self.i[orient].view(gloo.IndexBuffer)

            ########
            # Program
            self.program[orient] = gloo.Program(vertex, fragment)
            self.program[orient].bind(self.v[orient])
            model = np.eye(4, dtype=np.float32)
            glm.rotate(model, 180, 0, 0, 1)
            glm.rotate(model, self.modelZeroElevRotation[orient], *self.modelRotationAxes[orient])

            self.program[orient]['u_model'] = model

            self.program[orient]['u_view'] = glm.translation(0, 0.0, -1)
            self.program[orient]['viewport'] = transforms.Viewport()


    def checkInbox(self, dt):

        # Check if there is something in the pipe
        if not (self.pipeout.poll(timeout=.0001)):
            return

        # Receive data
        obj = self.pipeout.recv()

        # App close event
        if obj[0] == com.Display.ToDisplay.Close:
            self.window.close()

        # New display settings
        elif obj[0] == com.Display.ToDisplay.NewSettings:

            if self.program is None:
                return

            # Display parameters
            params = obj[1]

            # Set child viewport distance from center
            self.disp_vp_center_dist = params[com.Display.Settings.vp_center_dist]

            # Set global viewpoint position
            self.vp_global_pos = (params[com.Display.Settings.glob_x_pos], params[com.Display.Settings.glob_y_pos])

            # Set global display size
            self.vp_global_size = params[com.Display.Settings.glob_disp_size]

            # Set screen
            if not(self.window.get_fullscreen()):
                self.window.set_screen(params[com.Display.Settings.disp_screen_id])
                geo = self.window.get_screen().geometry()
                pos = geo.topLeft()
                self.window.set_position(pos.x(), pos.y())

            if self.window.get_fullscreen() != params[com.Display.Settings.disp_fullscreen]:
                print('Fullscreen state changed')
                self.window.set_fullscreen(params[com.Display.Settings.disp_fullscreen], screen=params[com.Display.Settings.disp_screen_id])

            # Set elevation
            for orient in self.modelRotationAxes:
                # Get current model
                model = self.program[orient]['u_model'].reshape((4,4))
                # Rotate back to zero elevation
                glm.rotate(model, -self.modelElevRotation[orient], *self.modelRotationAxes[orient])
                # Apply new rotation
                glm.rotate(model, params[com.Display.Settings.elev_angle], *self.modelRotationAxes[orient])
                # Save rotation for next back-rotation
                self.modelElevRotation[orient] = params[com.Display.Settings.elev_angle]
                # Set model
                self.program[orient]['u_model'] = model

            # Dispatch resize event
            self.window.dispatch_event('on_resize', self.window.width, self.window.height)

        # New stimulus to present
        elif obj[0] == com.Display.ToDisplay.SetNewStimulus:
            stimcls = obj[1]

            args = []
            if len(obj) > 2:
                args = obj[2]
            kwargs = dict()
            if len(obj) > 3:
                kwargs = obj[3]

            self.setupProgram()

            # Create stimulus instance
            self.stimulus = stimcls(*args, **kwargs)

            # Dispatch resize event
            self.window.dispatch_event('on_resize', self.window.width, self.window.height)


    def on_draw(self, dt):

        if self.program is None:
            return

        if self.stimulus is None:
            return

        # Fetch texture frame
        frame = self.stimulus.frame(dt)

        # Set texture
        self.program['ne']['u_texture'] = frame
        self.program['se']['u_texture'] = frame
        self.program['sw']['u_texture'] = frame
        self.program['nw']['u_texture'] = frame

        # Draw new display frame
        self.window.clear(color=(0.0, 0.0, 0.0, 1.0))  # black
        gl.glDisable(gl.GL_BLEND)
        gl.glEnable(gl.GL_DEPTH_TEST)
        self.program['ne'].draw(gl.GL_TRIANGLES, self.i['ne'])
        self.program['se'].draw(gl.GL_TRIANGLES, self.i['se'])
        self.program['sw'].draw(gl.GL_TRIANGLES, self.i['sw'])
        self.program['nw'].draw(gl.GL_TRIANGLES, self.i['nw'])

    def on_resize(self, width, height):

        if self.program is None:
            return

        # Fixes
        self.window._width = width
        self.window._height = height

        # Calculate child viewport size
        if width > height:
            length = height
        elif height > width:
            length = width
        else:
            length = height
        halflength = length // 2

        xpos = int(width * self.vp_global_pos[0])
        ypos = int(height * self.vp_global_pos[1])


        # Set viewports
        self.program['ne']['viewport']['global'] = (0, 0, width, height)
        self.program['ne']['viewport']['local'] = (halflength+xpos, halflength+ypos, halflength, halflength)

        self.program['se']['viewport']['global'] = (0, 0, width, height)
        self.program['se']['viewport']['local'] = (halflength+xpos, 0+ypos, halflength, halflength)

        self.program['sw']['viewport']['global'] = (0, 0, width, height)
        self.program['sw']['viewport']['local'] = (0+xpos, 0+ypos, halflength, halflength)

        self.program['nw']['viewport']['global'] = (0, 0, width, height)
        self.program['nw']['viewport']['local'] = (0+xpos, halflength+ypos, halflength, halflength)


        # Set projection
        dist = self.disp_vp_center_dist
        disp_size = np.array([-1.0, 1.0, -1.0, 1.0]) / self.vp_global_size

        self.program['ne']['u_projection'] = glm.ortho(*disp_size-dist, 0.0, 2.0)
        self.program['se']['u_projection'] = glm.ortho(*disp_size[:2]-dist, *disp_size[2:]+dist, 0.0, 2.0)
        self.program['sw']['u_projection'] = glm.ortho(*disp_size+dist, 0.0, 2.0)
        self.program['nw']['u_projection'] = glm.ortho(*disp_size[:2]+dist, *disp_size[2:]-dist, 0.0, 2.0)


        # Draw
        self.window.dispatch_event('on_draw', 0.0)
        self.window.swap()

    def on_init(self):
        if self.program is None:
            return

    def sendCloseInfo(self, fun):
        print('closing')
        fun()

def runDisplay(*args, **kwargs):

    display = Display(*args, **kwargs)

    # Schedule glumpy to check for new inputs (keep this as INfrequent as possible, rendering has priority)
    app.clock.schedule_interval(display.checkInbox, 0.1)
    app.run(framerate=60)