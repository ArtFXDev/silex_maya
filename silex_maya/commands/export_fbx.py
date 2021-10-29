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


class ExportFBX(CommandBase):
    """
    Export selection as FBX
    """

    parameters = {
        "file_path": {
            "label": "File path",
            "type": pathlib.Path,
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        # Get the output path
        directory = parameters.get("file_path")
        file_name = str(directory).split(os.path.sep)[-1]
        export_path = f"{directory}{os.path.sep}{file_name}.fbx"

        # Test if the user selected something
        def get_selection():
            return len(cmds.ls(sl=True))

        if not await Utils.wrapped_execute(action_query, get_selection):
            raise Exception("Could not export the selection: No selection detected")

        # Export the selection in OBJ
        os.makedirs(export_path, exist_ok=True)
        await Utils.wrapped_execute(
            action_query,
            cmds.file,
            export_path,
            exportSelected=True,
            pr=True,
            typ="FBX export",
        )

        # Test if the export worked
        if not os.path.exists(export_path):
            raise Exception("An error occured when exporting to FBX")

        return export_path
