name = "pyblish_lite"
version = "1.8.12"

authors = ["Pyblish"]
description = "A standalone GUI for Pyblish"

requires = [
    "maya",
]

build_system = "cmake"


def commands():
    env.QT_PREFERRED_BINDING = "PySide6"
    env.PYTHONPATH.prepend("{root}")

