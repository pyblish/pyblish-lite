cmake_minimum_required(VERSION 3.15)

include(RezBuild)

rez_install_dirs(
    pyblish_lite
    DESTINATION .
    LOCAL_SYMLINK
)