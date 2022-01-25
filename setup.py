#!/usr/bin/env python
from distutils.util import convert_path

from setuptools import setup

# Get version without sourcing silex module
# (to avoid importing dependencies yet to be installed)
main_ns = {}
with open(convert_path("silex_maya/__version__.py")) as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    version=main_ns["__version__"],
    python_requires="==3.7.*",
    entry_points={
        "silex_action_config": [
            "maya=silex_maya.config.entry_point:action_entry_points",
        ],
    },
    package_data={"": ["*.yaml", "*.yml", ".env"]},
    include_package_data=True,
)
