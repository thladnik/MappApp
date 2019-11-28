from MappApp_Stimulation_Protocol import StimulationProtocol

from stimuli.Checkerboard import Checkerboard
from stimuli.Grating import Grating

class Example01(StimulationProtocol):

    def __init__(self):
        super().__init__()

        self.addStimulus(Checkerboard, [16, 16], dict(), duration=10)
        self.addStimulus(Grating, [], dict(), duration=None)
        self.addStimulus(Checkerboard, [8, 12], dict(), duration=None)
