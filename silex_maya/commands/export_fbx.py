from __future__ import annotations
import typing
from typing import Any, Dict

from silex_maya.utils.utils import Utils
from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.dialogs import Dialogs
from silex_maya.utils.utils import Utils

import maya.cmds as cmds
import os
import pathlib


class Export_fbx(CommandBase):
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
        path = parameters.get('file_path')

        cmds.file(path, exportSelected=True, pr=True, typ="FBX export")

        if os.path.exists(path):
            Dialogs.inform('Export succeded')
