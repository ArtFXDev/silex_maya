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
        "file_path": {
            "label": "File path",
            "type": pathlib.Path,
            "value": None,
        }
    }

    @ CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        extension = await gazu.files.get_output_type_by_name("V-Ray Scene File")

        directory: str = parameters.get("file_path")
        file_name: str = str(directory).split(os.path.sep)[-1]
        export_path: str = f"{directory}{os.path.sep}{file_name}.{extension}"

        await Utils.wrapped_execute(action_query, cmds.file, export_path, options=True, force=True,
                                    pr=True, ea=True, typ="V-Ray Scene")

        # Test if the export worked
        import time
        time.sleep(1)

        if not os.path.exists(export_path):
            raise Exception(
                f"An error occured while exporting {export_path} to vrscene")
        return export_path
