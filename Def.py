"""
MappApp ./Def.py - Definitions required to run the program.
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


################################
# Environment settings

class EnvTypes:
    Dev        = 'dev'
    Production = 'production'

Env = EnvTypes.Production


################################
# Subfolder definitions

class Path:
    Config   = 'configs'
    Log      = 'logs'
    Model    = 'models'
    Output   = 'output'
    Protocol = 'protocols'
    Sample   = 'samples'
    Shader   = 'shaders'
    Task     = 'tasks'


################################
# Process names

class Process:
    Camera     = 'Camera'
    Controller = 'Controller'
    Display    = 'Display'
    GUI        = 'Gui'
    IO         = 'IO'
    Logger     = 'Logger'
    Worker     = 'Worker'


################################
# Process states

class State:
    na               = 0
    STOPPED          = 99
    starting         = 10
    PREPARE_PROTOCOL = 30
    WAIT_FOR_PHASE   = 31
    PREPARE_PHASE    = 32
    READY            = 33
    PHASE_END        = 37
    PROTOCOL_END     = 39
    IDLE             = 20
    RUNNING          = 41
    standby          = 42

################################
# IPC signals

class Signal:
    UpdateProperty  = 10
    RPC             = 20
    Query           = 30
    Shutdown        = 99
    ConfirmShutdown = 100


################################
# Configuration key definitions

########
# Camera

class CameraCfg:
    name = 'camera'

    # Use camera
    use          = 'bool_use'

    # Camera configuration
    manufacturer = 'str_manufacturer'
    model        = 'str_model'
    format       = 'str_format'
    res_x        = 'int_resolution_x'
    res_y        = 'int_resolution_y'
    fps          = 'int_prop_fps'
    exposure     = 'float_prop_exposure'
    gain         = 'float_prop_gain'

    # Buffers
    buffers      = 'list_buffers'


########
# Display

class DisplayCfg:
    name = 'display'

    # Use display
    use                    = 'bool_use'
    type                   = 'str_type'

    fps                    = 'int_fps'

    # Window settings
    window_screen_id       = 'int_window_screen_id'
    window_fullscreen      = 'bool_window_fullscreen'
    window_width           = 'int_window_width'
    window_height          = 'int_window_height'
    window_pos_x           = 'int_window_pos_x'
    window_pos_y           = 'int_window_pos_y'

    # Calibration settings
    pos_glob_x_pos         = 'float_pos_glob_x_pos'
    pos_glob_y_pos         = 'float_pos_glob_y_pos'
    pos_glob_radial_offset = 'float_pos_glob_radial_offset'

    view_elev_angle        = 'float_view_elev_angle'
    view_azim_angle        = 'float_view_azim_angle'
    view_distance          = 'float_view_origin_distance'
    view_scale             = 'float_view_scale'


########
# GUI

class GuiCfg:
    name = 'gui'

    use         = 'bool_use'

    # Addons
    addons      = 'list_addons'


########
# IO

class IoCfg:
    name = 'io'

    use          = 'bool_use'
    device_type  = 'str_device_type'
    device_model = 'str_device_model'
    device_port  = 'str_device_comport'
    digital_pins = 'list_digital_pins'
    analog_pins  = 'list_analog_pins'

    buffers = 'list_buffers'


########
# Recording

class RecCfg:
    name = 'recording'

    enabled         = 'bool_enabled'

    # Active buffers
    buffers         = 'list_buffers'


################################
# Controls

########
# Recording

class RecCtrl:
    active    = 'recording_active'
    folder    = 'current_folder'

################################
# Protocol

class ProtocolCtrl:
    name             = 'current_protocol'
    phase_id         = 'current_phase'
    phase_start      = 'phase_start_time'
    phase_stop       = 'phase_stop_time'

