from __future__ import annotations

import typing
from typing import Any, Dict

from genericpath import exists
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

import gazu
from maya import cmds


class ExportOBJ(CommandBase):
    """
    Export selection as obj
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
        "root_name": {
            "label": "Out Object Name",
            "type": str,
            "value": "",
            "hide": False,
        },
    }

    async def _prompt_info_parameter(
        self, action_query: ActionQuery, message: str, level: str = "warning"
    ) -> pathlib.Path:
        """
        Helper to prompt the user a label
        """

        # Create a new parameter to prompt label
        info_parameter = ParameterBuffer(
            type=TextParameterMeta(level),
            name="Info",
            label="Info",
            value=f"Warning : {message}",
        )

        # Prompt the user with a label
        prompt = await self.prompt_user(action_query, {"info": info_parameter})

        return prompt["info"]

    def selected_objects(self):
        """Get selection in open scene"""

        # Get current selection
        selected = cmds.ls(sl=True, long=True) or []
        selected.sort(key=len, reverse=True)  # reverse

        return selected

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        # Get the output path
        directory = parameters.get("directory")
        file_name = parameters.get("file_name")
        root_name = parameters.get("root_name")

        # Authorized types
        authorized_types = ["mesh", "transform"]

        # Get selection
        selected = await utils.wrapped_execute(
            action_query, lambda: self.selected_objects()
        )
        selected = await selected

        # Exclude unauthorized types
        selected = [
            item
            for item in selected
            if cmds.objectType(item.split("|")[-1]) in authorized_types
        ]

        while len(selected) != 1:
            await self._prompt_info_parameter(
                action_query,
                "Could not export the selection: Select only one mesh component.",
            )
            # Get selection
            selected = await utils.wrapped_execute(
                action_query, lambda: self.selected_objects()
            )
            selected = await selected

            # Exclude unauthorized types
            selected = [
                item
                for item in selected
                if cmds.objectType(item.split("|")[-1]) in authorized_types
            ]

        # Export the selection in OBJ
        os.makedirs(directory, exist_ok=True)

        # Create export path path
        export_path = (
            directory / f"{file_name}_{root_name}"
            if root_name
            else directory / f"{file_name}"
        )
        extension = await gazu.files.get_output_type_by_name("obj")
        export_path = export_path.with_suffix(f".{extension['short_name']}")

        # Export in OBJ
        await utils.wrapped_execute(
            action_query,
            cmds.file,
            export_path,
            exportSelected=True,
            pr=True,
            type="OBJexport",
        )

        return str(export_path)
