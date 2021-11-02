from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_maya.utils.utils import Utils
from silex_client.utils.log import logger


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import maya.cmds as cmds
import os
import pathlib
import shutil
import tempfile


class ExportOBJ(CommandBase):
    """
    Export selection as obj
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
        directory: str = parameters.get("file_path")
        file_name: str = str(directory).split(os.path.sep)[-1]
        temp_path: str = f"{tempfile.gettempdir()}{os.path.sep}{os.path.sep}{file_name}.obj"
        export_path: str = f"{directory}{os.path.sep}{file_name}.obj"

        # Test if the user selected something
        def get_selection() -> int:
            return len(cmds.ls(sl=True))

        if not await Utils.wrapped_execute(action_query, get_selection):
            raise Exception(
                "Could not export the selection: No selection detected")

        # Export the selection in OBJ
        await Utils.wrapped_execute(
            action_query,
            cmds.file,
            temp_path,
            exportSelected=True,
            pr=True,
            typ="OBJexport",
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
