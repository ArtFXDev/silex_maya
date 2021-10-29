from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.dialogs import Dialogs
from silex_maya.utils.utils import Utils

import maya.cmds as cmds
import os
import pathlib


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
        def export_vrscene(path: str) -> None:

            cmds.file(path, options=True, force=True,
                      pr=True, ea=True, typ="V-Ray Scene")

            if os.path.exists(path):
                Dialogs.inform('Export SUCCEEDED !')
            else:
                Dialogs.error('ERROR : Export FAILD !')

        path: str = parameters.get('file_path')

        await Utils.wrapped_execute(action_query, lambda: export_vrscene(path))
