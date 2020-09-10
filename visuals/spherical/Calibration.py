"""
MappApp ./visuals/Calibration.py - Checkerboard visuals
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

from glumpy import gl
import numpy as np

from Visuals import SphericalVisual
from models import BasicSphere
from Shader import BasicFileShader

class BlackWhiteCheckerboard(SphericalVisual):

    u_rows = 'u_rows'
    u_cols = 'u_cols'

    parameters = {u_rows: None, u_cols: None}

    def __init__(self, *args, **params):
        """Black-and-white checkerboard for calibration.

        :param protocol: protocol of which stimulus is currently part of
        :param rows: number of rows on checkerboard
        :param cols: number of columns on checkerboard
        """
        SphericalVisual.__init__(self, *args)

        self.sphere = self.addModel('sphere',
                                    BasicSphere.UVSphere,
                                    theta_lvls=100, phi_lvls=50, theta_range=2*np.pi, upper_phi=np.pi/2)
        self.sphere.createBuffers()
        self.checker = self.addProgram('sphere',
                                       BasicFileShader().addShaderFile('spherical/checkerboard.vert').read(),
                                       BasicFileShader().addShaderFile('spherical/checkerboard.frag').read())
        self.checker.bind(self.sphere.vertexBuffer)

        self.update(**params)

    def render(self):
        self.checker.draw(gl.GL_TRIANGLES, self.sphere.indexBuffer)

    def update(self, **params):

        self.parameters.update({k : p for k, p in params.items() if not(p is None)})
        for k, p in self.parameters.items():
            if hasattr(self, 'parse_{}'.format(k)):
                self.checker[k] = getattr(self, 'parse_{}'.format(k))(p)
            else:
                self.checker[k] = p
