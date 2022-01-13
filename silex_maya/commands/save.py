from __future__ import annotations
import typing
from typing import Any, Dict

from silex_maya.utils.utils import Utils
from silex_client.action.command_base import CommandBase
import logging

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os
import maya.cmds as cmds


class Save(CommandBase):
    """
    Save current scene with context as path
    """

    parameters = {"file_path": {"label": "filename", "type": str, "hide": False}}

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        def save(file_path: str):
            cmds.file(rename=file_path)
            cmds.file(save=True, type="mayaAscii", prompt=False)

        file_path = parameters["file_path"]
        logger.info(file_path)
        if os.path.splitext(file_path)[1] != ".ma":
            file_path = f"{os.path.splitext(file_path)[0]}.ma"

        logger.info("Saving scene to %s", file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        await Utils.wrapped_execute(action_query, save, file_path=file_path)

        return {"new_path": file_path}
