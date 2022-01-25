from __future__ import annotations

import typing
from concurrent.futures import Future
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import TextParameterMeta

from silex_maya.utils import utils

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import logging
import os
import pathlib

import gazu.files
import maya.cmds as cmds


class ExportMa(CommandBase):
    """
    Export selection as ma
    """

    parameters = {
        "directory": {
            "label": "File directory",
            "type": pathlib.Path,
            "value": None,
        },
        "file_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": None,
        },
    }

    async def _prompt_warning(self, action_query: ActionQuery) -> bool:
        """
        Helper to prompt the user a label
        """

        # Check if export is valid
        while True:
            # Create a new parameter to prompt label
            info_parameter = ParameterBuffer(
                type=TextParameterMeta("warning"),
                name="Info",
                label="Info",
            )

            bool_parameter = ParameterBuffer(
                type=bool, name="full_scene", label="Publish full scene", value=True
            )

            # Prompt the user with a label
            prompt: Dict[str, Any] = await self.prompt_user(
                action_query, {"info": info_parameter, "full_scene": bool_parameter}
            )

            # Get selected objects
            future: Any = await utils.wrapped_execute(action_query, cmds.ls, sl=1)
            slection_list = await future

            if len(slection_list) or prompt["full_scene"]:
                return True

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        directory: pathlib.Path = parameters[
            "directory"
        ]  # Directory parameter is temp directory
        file_name: pathlib.Path = parameters["file_name"]
        full_scene: bool = False

        extension = await gazu.files.get_output_type_by_name("ma")
        export_path: pathlib.Path = (directory / file_name).with_suffix(
            f".{extension['short_name']}"
        )

        # Export the selection in ma
        future: Future = await utils.wrapped_execute(action_query, cmds.ls, sl=1)
        slection_list: List[str] = future.result()

        # Prompt warning
        if not len(slection_list):
            full_scene = await self._prompt_warning(action_query)

        # Export in temps directory
        os.makedirs(directory, exist_ok=True)
        await utils.wrapped_execute(
            action_query,
            cmds.file,
            export_path,
            es=not (full_scene),
            ea=full_scene,
            pr=True,
            typ="mayaAscii",
        )

        return export_path

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Warning message
        if "info" in parameters:
            if parameters.get("full_scene", False):
                self.command_buffer.parameters["info"].type = TextParameterMeta("info")
                self.command_buffer.parameters[
                    "info"
                ].value = "No selection detected -> Please select something or publish full scene"
            else:
                self.command_buffer.parameters["info"].type = TextParameterMeta(
                    "warning"
                )
                self.command_buffer.parameters[
                    "info"
                ].value = "Select something to publish"
