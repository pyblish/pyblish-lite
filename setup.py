import os
import imp
from setuptools import setup, find_packages

version_file = os.path.abspath("pyblish_lite/version.py")
version_mod = imp.load_source("version", version_file)
version = version_mod.version


classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.5",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Utilities"
]


setup(
    name="pyblish-lite",
    version=version,
    description="Lightweight graphical user interface to Pyblish",
    long_description="See https://github.com/pyblish/pyblish-lite",
    author="Abstract Factory and Contributors",
    author_email="marcus@abstractfactory.com",
    url="https://github.com/pyblish/pyblish-lite",
    license="LGPL",
    packages=find_packages(),
    zip_safe=False,
    classifiers=classifiers,
    package_data={
        "pyblish_lite": [
            "*.css",
            "img/*.png",
            "font/fontawesome/*.ttf",
            "font/opensans/*.ttf"
        ],
    },
    install_requires=[
        "pyblish-base>=1.4"
    ],
)
