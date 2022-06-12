from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import ListParameterMeta
from silex_maya.utils.thread import execute_in_main_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os

import maya.cmds as cmds


class Save(CommandBase):
    """
    Save current scene with context as path
    """

    parameters = {
        "file_paths": {
            "label": "filename",
            "type": ListParameterMeta(str),
            "hide": False,
        }
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        file_paths = parameters["file_paths"]

        def save(file_path: str):
            cmds.file(rename=file_path)
            cmds.file(save=True, type="mayaAscii")

        for file_path in file_paths:
            if os.path.splitext(file_path)[1] != ".ma":
                file_path = f"{os.path.splitext(file_path)[0]}.ma"

            logger.info("Saving scene to %s", file_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            await execute_in_main_thread(save, file_path=file_path)

            file_paths[file_paths.index(file_path)] = file_path

        return {"new_path": file_paths}
