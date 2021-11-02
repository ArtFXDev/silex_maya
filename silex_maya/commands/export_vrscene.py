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
import tempfile
import shutil


class ExportVrscene(CommandBase):
    """
    Export selection as obj
    """

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

        directory: str = parameters.get("file_path")
        file_name: str = str(directory).split(os.path.sep)[-1]
        temp_path: str = f"{tempfile.gettempdir()}{os.path.sep}{os.path.sep}{file_name}.vrscene"
        export_path: str = f"{directory}{os.path.sep}{file_name}.vrscene"

        await Utils.wrapped_execute(action_query, cmds.file, temp_path, options=True, force=True,
                                    pr=True, ea=True, typ="V-Ray Scene")

        # Test if the export worked
        import time
        time.sleep(1)
        if not os.path.exists(temp_path):
            raise Exception("An error occured when exporting to OBJ")

        # Move to export destination
        async def save_from_temp():
            export = pathlib.Path(export_path)
            export_dir = export.parents[0]

            os.makedirs(export_dir, exist_ok=True)
            shutil.copy2(temp_path, export_path)
            os.remove(temp_path)

        await save_from_temp()

        return export_path
