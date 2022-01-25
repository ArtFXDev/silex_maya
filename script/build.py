import contextlib
import os
import shutil
import sys


def build(source_path, build_path, install_path, targets):
    """
    Build the rez package and install it if requested
    """
    src = os.path.join(source_path, "silex_maya")
    startup = os.path.join(source_path, "startup")
    package = os.path.join(source_path, "package.py")

    # Clear the build folder, if a previous build were made
    if os.path.exists(build_path):
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree(os.path.join(build_path, "silex_maya"))
            shutil.rmtree(os.path.join(build_path, "startup"))
            os.remove(os.path.join(build_path, "package.py"))

    # Copy the source to the build location
    shutil.copytree(src, os.path.join(build_path, "silex_maya"))
    shutil.copytree(startup, os.path.join(build_path, "startup"))
    shutil.copy(package, build_path)

    if "install" in (targets or []):
        # Clear the install folder if a previous install where already here
        if os.path.exists(install_path):
            with contextlib.suppress(FileNotFoundError):
                shutil.rmtree(install_path)

        # Copy the source to the install location
        shutil.copytree(src, os.path.join(install_path, "silex_maya"))
        shutil.copytree(startup, os.path.join(install_path, "startup"))
        shutil.copy(package, install_path)


if __name__ == "__main__":
    build(
        source_path=os.environ["REZ_BUILD_SOURCE_PATH"],
        build_path=os.environ["REZ_BUILD_PATH"],
        install_path=os.environ["REZ_BUILD_INSTALL_PATH"],
        targets=sys.argv[1:],
    )
