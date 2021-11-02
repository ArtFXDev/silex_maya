from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.utils import Utils

import maya.cmds as cmds
import os
import pathlib
import shutil
import tempfile


class ExportABC(CommandBase):
    """
    Export selection as obj
    """

    parameters = {
        "file_path": {
            "label": "File path",
            "type": pathlib.Path,
            "value": None,
        },
        "start_frame": {
            "label": "Start Frame",
            "type": int,
        },
        "end_frame": {
            "label": "End Frame",
            "type": int,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        # Get the output path and range variable
        directory: str = parameters.get("file_path")
        file_name: str = str(directory).split(os.path.sep)[-1]
        temp_path: str = f"{tempfile.gettempdir()}{os.path.sep}{os.path.sep}{file_name}.abc"
        export_path: str = f"{directory}{os.path.sep}{file_name}.abc"
        start: int = parameters.get("start_frame")
        end: int = parameters.get("end_frame")

        def export_abc(start: int, end: int, path: str) -> None:

            root: str = cmds.ls(sl=True, l=True)[0]

            if root is None:
                raise Exception("ERROR: No selection detected")

            cmds.AbcExport(
                j="-uvWrite -dataFormat ogawa -root {} -frameRange {} {} -file {}".format(
                    root, start, end, path
                )
            )

        await Utils.wrapped_execute(
            action_query, lambda: export_abc(start, end, temp_path)
        )

        # Test if the export worked
        import time
        time.sleep(1)

        if not os.path.exists(temp_path):
            raise Exception("An error occured when exporting to OBJ")

        # Move to export destination
        async def save_from_temp():
            export: str = pathlib.Path(export_path)
            export_dir: str = export.parents[0]

            os.makedirs(export_dir, exist_ok=True)
            shutil.copy2(temp_path, export_path)
            os.remove(temp_path)

        await save_from_temp()

        return export_path
