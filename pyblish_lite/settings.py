from .util import env_variable_to_bool

# Customize the window of the pyblish-lite window.
WindowTitle = "Pyblish"

# Customize whether to show label names for plugins.
UseLabel = True

# Customize which tab to start on. Possible choices are: "artist", "overview"
# and "terminal".
InitialTab = "artist"

# Customize the window size.
WindowSize = (430, 600)

TerminalFilters = {
    "info": True,
    "log_debug": True,
    "log_info": True,
    "log_warning": True,
    "log_error": True,
    "log_critical": True,
    "traceback": True,
}

# Allow animations in GUI
Animated = env_variable_to_bool("PYBLISH_LITE_ANIMATED", True)
