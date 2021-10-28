# pylint: skip-file
name = "silex_maya"
version = "0.1.0"

authors = ["ArtFx TD gang"]

description = """
    Set of python module and maya config to integrate maya in the silex pipeline
    Part of the Silex ecosystem
    """

vcs = "git"

requires = ["silex_client", "maya", "python-3.7"]

build_command = "python {root}/script/build.py {install}"


def commands():
    """
    Set the environment variables for silex_maya
    """
    env.SILEX_ACTION_CONFIG.prepend("{root}/config")
    env.PYTHONPATH.append("{root}")
    env.PYTHONPATH.append("{root}/startup")
