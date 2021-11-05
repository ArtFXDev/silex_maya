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


class ExportVrscene(CommandBase):
    """
    Export selection as v-ray scene
    """

    # set camera list
    cam_list = cmds.listCameras()
    cam_list.append('No camera')

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

    @ CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        directory: str = parameters.get("file_path")
        file_name: str = parameters.get("file_name")
        
        # Check for extension
        if "." in file_name:
            file_name = file_name.split('.')[0]
          
        export_path: str = f"{directory}{os.path.sep}{file_name}.vrscene"

        # Export the selection in OBJ
        os.makedirs(directory, exist_ok=True)


        await Utils.wrapped_execute(action_query, cmds.file, export_path, options=True, force=True,
                                    pr=True, ea=True, typ="V-Ray Scene")

        # Test if the export worked
        import time
        time.sleep(1)

        if not os.path.exists(export_path):
            raise Exception(
                f"An error occured while exporting {export_path} to vrscene")
        return export_path
