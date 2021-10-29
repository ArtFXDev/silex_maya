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


class ExportObj(CommandBase):
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

        def export_obj(path: str) -> None:

            if not len(cmds.ls(sl=True)):
                raise Exception('ERROR: No selection detected')

            cmds.workspace(fileRule=['abc', path])
            cmds.file(path, exportSelected=True, pr=True, typ="OBJexport")

            if os.path.exists(path):
                Dialogs.inform('Export SUCCEEDED !')
            else:
                Dialogs.error('ERROR : Export FAILD !')

        path: str = parameters.get('file_path')

        await Utils.wrapped_execute(action_query, lambda: export_obj(path))
