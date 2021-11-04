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
import gazu.files


class ExportABC(CommandBase):
    """
    Export selection as abc
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

        extension = await gazu.files.get_output_type_by_name("Alembic")


        # Get the output path and range variable
        directory: str = parameters.get("file_path")
        file_name: str = str(directory).split(os.path.sep)[-1]
        export_path: str = f"{directory}{os.path.sep}{file_name}.{extension}"
        start: int = parameters.get("start_frame")
        end: int = parameters.get("end_frame")

        def export_abc(start: int, end: int, path: str) -> None:

            # Get root
            root: str = cmds.ls(sl=True, l=True)[0]

            # Check selected root
            if root is None:
                raise Exception("ERROR: No root found")

            cmds.AbcExport(
                j=f"-uvWrite -dataFormat ogawa -root {root} -frameRange {start} {end} -file {path}"
            )

        await Utils.wrapped_execute(
            action_query, lambda: export_abc(start, end, export_path)
        )

        # Test if the export worked
        import time
        time.sleep(1)

        if not os.path.exists(export_path):
            raise Exception(
                f"An error occured while exporting {export_path} to alembic")

        return export_path
