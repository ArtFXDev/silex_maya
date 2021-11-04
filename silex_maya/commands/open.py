from __future__ import annotations
import typing
from typing import Any, Dict

import pathlib
from silex_maya.utils.utils import Utils
from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os
import maya.cmds as cmds


class Open(CommandBase):
    """
    Open the given scene file
    """

    parameters = {
        "file_path": {
            "label": "filename",
            "type": pathlib.Path,
            "value": None,
        }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        file_path = parameters["file_path"]
        if not os.path.exists(file_path):
            raise Exception(
                "Could not open the file {file_path}: The file does not exists"
            )

        def open(file_path: str):
            cmds.file(save=True)
            cmds.file(file_path, o=True)

        await Utils.wrapped_execute(
            action_query, open, file_path=parameters["file_path"]
        )
