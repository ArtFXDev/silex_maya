from __future__ import annotations

import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import TextParameterMeta
from silex_maya.utils.thread import execute_in_main_thread

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
                type=TextParameterMeta("info"),
                name="Info",
                label="Info",
            )

            bool_parameter = ParameterBuffer(
                type=bool, name="selection", label="Publish selection", value=True
            )

            # Prompt the user with a label
            prompt: Dict[str, Any] = await self.prompt_user(
                action_query, {"info": info_parameter, "selection": bool_parameter}
            )

            # Get selected objects
            selection_list: Any = await execute_in_main_thread(cmds.ls, sl=1)

            if len(selection_list) and prompt["selection"]:
                return True
            else:
                return False

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
        selection: bool = False

        extension = await gazu.files.get_output_type_by_name("ma")
        export_path: pathlib.Path = (directory / file_name).with_suffix(
            f".{extension['short_name']}"
        )

        # Export the selection in ma
        selection_list: List[str] = await execute_in_main_thread(cmds.ls, sl=1)

        # Prompt warning
        if len(selection_list):
            selection = await self._prompt_warning(action_query)

        # Export in temps directory
        directory.mkdir(parents=True, exist_ok=True)
        if selection:
            await execute_in_main_thread(
                cmds.file,
                export_path,
                es=selection,
                ea=not (selection),
                pr=True,
                typ="mayaAscii",
            )
        else:
            current_path = await execute_in_main_thread(cmds.file, q=True, sn=True)
            if current_path and pathlib.Path(current_path).exists():
                await execute_in_main_thread(cmds.file, save=True)

            await execute_in_main_thread(cmds.file, rename=export_path)
            await execute_in_main_thread(cmds.file, save=True, typ="mayaAscii")

            if current_path and pathlib.Path(current_path).exists():
                await execute_in_main_thread(cmds.file, rename=current_path)
            else:
                await execute_in_main_thread(cmds.file, rename="untitled")

        return export_path

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Warning message
        if "info" in parameters:
            if parameters["selection"]:
                self.command_buffer.parameters["info"].type = TextParameterMeta("info")
                self.command_buffer.parameters["info"].value = (
                    "You are about to export a selection, continue ?\n"
                    + "(renderlayers are not exported when exporting the selection)"
                )
            else:
                self.command_buffer.parameters["info"].type = TextParameterMeta("info")
                self.command_buffer.parameters[
                    "info"
                ].value = "Publish full scene (ignore selection)"
