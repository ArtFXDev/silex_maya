from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase

from silex_maya.utils import utils

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os

from maya import cmds


class Open(CommandBase):
    """
    Open the given scene file
    """

    parameters = {
        "file_path": {
            "label": "filename",
            "type": pathlib.Path,
            "value": None,
        },
        "save": {
            "label": "Save before opening",
            "type": bool,
            "value": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        file_path = parameters["file_path"]

        # First get the current file name
        current_file = await utils.wrapped_execute(
            action_query, cmds.file, q=True, sn=True, prompt=False
        )
        current_file = await current_file

        # Test if the scene that we have to open exists
        if not os.path.exists(file_path) or not os.path.isabs(file_path):
            logger.error("Could not open %s: The file does not exists", file_path)
            return {"old_path": current_file, "new_path": current_file}

        # Define the function that will open the scene
        def open(file_path: str, force: bool = False):
            # Check if there is some modifications to save
            file_state = cmds.file(q=True, modified=True)
            current_file = cmds.file(q=True, sn=True)

            # Don't open the scene if it is already open
            if pathlib.Path(current_file) == file_path:
                return
            # Save the current scene before openning a new one
            if file_state and current_file and parameters["save"]:
                cmds.file(save=True)
            # If the scene has unsaved changes we must force the open
            elif file_state:
                force = True
            cmds.file(file_path, o=True, force=force)

        # Execute the open function in the main thread
        logger.info("Openning file %s", file_path)
        await utils.wrapped_execute(action_query, open, file_path=file_path)

        return {"old_path": current_file, "new_path": parameters["file_path"]}
