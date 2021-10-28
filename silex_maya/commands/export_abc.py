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


class Export_abc(CommandBase):
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

        path: str = parameters.get('file_path')

        start: int = parameters.get('start_frame')
        end: int = parameters.get('end_frame')

        root: str = str(cmds.ls(selection=True)[0])

        command: str = "-frameRange " + start + " " + end + \
            " -uvWrite -worldSpace " + root + " -file " + path
        cmds.AbcExport(j=command)

        if os.path.exists(path):
            Dialogs.inform('Export SUCCEDE !')
        else:
            Dialogs.error('ERROR : Export FAILD !')
