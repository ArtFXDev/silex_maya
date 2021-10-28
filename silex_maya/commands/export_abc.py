from __future__ import annotations
import typing
from typing import Any, Dict

from silex_maya.utils.utils import Utils
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import RangeParameterMeta

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
        "range": {
            "label": "Range",
            "type": RangeParameterMeta(1, 475, 1),
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        path = parameters.get('file_path')

        start = "0"
        end = "100"
        root = str(cmds.ls(selection=True)[0])

        command = "-frameRange " + start + " " + end + \
            " -uvWrite -worldSpace " + root + " -file " + path
        cmds.AbcExport(j=command)

        if os.path.exists(path):
            Dialogs.inform('Export succeded')
