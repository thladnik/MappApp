"""
MappApp ./protocols/Calibration.py - Protocols for calibration of spherical visual stimulation setup.
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

from Protocol import StaticStimulationProtocol

from stimuli.planar.Calibration import Checkerboard

class CheckerboardProtocol(StaticStimulationProtocol):

    _name = 'PlaneCalibration'

    def __init__(self, _glWindow):
        super().__init__(_glWindow)

        self.addStimulus(Checkerboard, dict())
