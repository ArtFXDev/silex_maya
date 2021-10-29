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


class ExportAbc(CommandBase):
    """
    Export selection as obj
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

        def export_abc(start: int, end: int, path: str) -> None:

            root: str = cmds.ls(sl=True, l=True)[0]

            if root is None:
                raise Exception('ERROR: No selection detected')

            cmds.workspace(fileRule=['abc', path])

            cmds.AbcExport(
                j="-uvWrite -dataFormat ogawa -root {} -frameRange {} {} -file {}".format(root, start, end, path))

            if os.path.exists(path):
                Dialogs.inform('Export SUCCEEDED !')
            else:
                Dialogs.error('ERROR : Export FAILD !')

        path: str = parameters.get('file_path')

        start: int = parameters.get('start_frame')
        end: int = parameters.get('end_frame')

        await Utils.wrapped_execute(action_query, lambda: export_abc(start, end, path))
