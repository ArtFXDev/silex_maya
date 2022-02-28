import contextlib

from silex_client.cli.parser import main

if __name__ == "__main__":
    with contextlib.suppress(ImportError, RuntimeError):
        import maya.standalone

        maya.standalone.initialize(name="python")

    main()
