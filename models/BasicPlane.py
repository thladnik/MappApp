"""
MappApp ./models/BasicPlane.py - Basic planar models for re-use.
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
########
## !!! BE EXTREMELY CAREFUL WHEN EDITING THESE MODELS !!!
## Any changes will affect all stimuli associated with the models!
####
########

import numpy as np

from Model import PlaneModel

class VerticalXYPlane(PlaneModel):

    def __init__(self, sample_rate = 100, **kwargs):
        PlaneModel.__init__(self, **kwargs)

        x = np.linspace(-1.0, 1.0, sample_rate, endpoint=True)
        y = np.linspace(-1.0, 1.0, sample_rate, endpoint=True)


        coordsX, coordsY = np.meshgrid(x, y)
        coordsX = coordsX.flatten()
        coordsY = coordsY.flatten()

        self.a_position = np.array([coordsX, coordsY, np.zeros(sample_rate**2)]).T

        ### Set indices
        idcs = list()
        for i in np.arange(sample_rate):
            for j in np.arange(sample_rate):
                idcs.append([i * sample_rate + j, i * sample_rate + j + 1, (i+1) * sample_rate + j + 1])
                idcs.append([i * sample_rate + j, (i+1) * sample_rate + j, (i+1) * sample_rate + j + 1])
        self.indices = np.array(idcs).flatten()

