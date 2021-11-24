from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import RangeParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.utils import Utils

import maya.cmds as cmds
import os
import pathlib
import logging

class ExportMa(CommandBase):
    """
    Export selection as ma
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
        "range": {
            "label": "Range",
            "type": RangeParameterMeta(1, 475, 1),
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.logger
    ):

        def export_ma(path: str) -> None:

            if not len(cmds.ls(sl=True)):
                raise Exception('ERROR: No selection detected')

            cmds.file(path, exportSelected=True, pr=True, typ="mayaAscii")

        directory: str = str(parameters.get("file_dir"))
        file_name: str = str(parameters.get("file_name"))
        
        # Check for extension
        if "." in file_name:
            file_name = file_name.split('.')[0]
          
        export_path: str = f"{directory}{os.path.sep}{file_name}.ma"

        # Export the selection in OBJ
        os.makedirs(directory, exist_ok=True)


        await Utils.wrapped_execute(action_query, lambda: export_ma(export_path))

        # Test if the export worked
        import time
        time.sleep(1)

        if not os.path.exists(export_path):
            raise Exception(
                f"An error occured while exporting {export_path} to ma")
        return export_path
