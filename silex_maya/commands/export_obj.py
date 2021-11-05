from __future__ import annotations
from genericpath import exists
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger
from silex_maya.utils.utils import Utils


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import maya.cmds as cmds
import os
import pathlib


class ExportOBJ(CommandBase):
    """
    Export selection as obj
    """

    parameters = {
        "file_dir": {
            "label": "File directory",
            "type": pathlib.Path,
            "value": None,
        },
        "file_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        # Get the output path
        directory: str = str(parameters.get("file_dir"))
        file_name: str = str(parameters.get("file_name"))

        # Check for extension
        if "." in file_name:
            file_name = file_name.split('.')[0]

        export_path: str = f"{directory}{os.path.sep}{file_name}.obj"

        # Test if the user selected something
        def get_selection() -> int:
            return len(cmds.ls(sl=True))

        if not await Utils.wrapped_execute(action_query, get_selection):
            raise Exception(
                "Could not export the selection: No selection detected")


        # Export the selection in OBJ
        os.makedirs(directory, exist_ok=True)

        await Utils.wrapped_execute(
            action_query,
            cmds.file,
            export_path,
            exportSelected=True,
            pr=True,
            typ="OBJexport",
        )

        # Test if the export worked
        import time
        time.sleep(1)

        if not os.path.exists(export_path):
            raise Exception(
                f"An error occured while exporting {export_path} to OBJ")

        return export_path
