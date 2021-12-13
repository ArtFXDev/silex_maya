import contextlib
from silex_client.cli.parser import main

with contextlib.suppress(ImportError, RuntimeError):
    import maya.standalone
    maya.standalone.initialize(name="python")

if __name__ == "__main__":
    main()
