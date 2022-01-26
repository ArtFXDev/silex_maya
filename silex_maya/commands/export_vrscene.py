from __future__ import annotations

import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils import thread as thread_client
from silex_client.utils.command import CommandBuilder
from silex_client.utils.parameter_types import (
    MultipleSelectParameterMeta,
    TextParameterMeta,
)

from silex_maya.utils import thread as thread_maya

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from maya import cmds
import gazu.files
import os
import pathlib
import subprocess
import logging

import gazu.files
from maya import cmds


class ExportVrscene(CommandBase):
    """
    Export selection as v-ray scene
    """

    parameters = {
        "directory": {
            "label": "File directory",
            "type": pathlib.Path,
            "value": None,
            "hide": True,
        },
        "file_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": None,
            "hide": True,
        },
        "render_layers": {
            "label": "Select render layers",
            "type": MultipleSelectParameterMeta(),
            "value": ['defaultRenderLayer'],

        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        directory: pathlib.Path = parameters["directory"]
        file_name: pathlib.Path = parameters["file_name"]
        render_layers: List[str] = parameters["render_layers"]
        extension = await gazu.files.get_output_type_by_name("vrscene")

        # Create temporary directory
        os.makedirs(directory, exist_ok=True)

        # Batch: Export vrscene for each render layer
        output_files: List[pathlib.Path] = list()
        command_label = self.command_buffer.label

        for index, layer in enumerate(render_layers):
            new_label = f"{command_label}: ({index + 1}/{len(render_layers)})"
            self.command_buffer.label = new_label
            await action_query.async_update_websocket(apply_response=False)

            output_name: pathlib.Path = pathlib.Path(f"{file_name}_{layer}")
            output_path: pathlib.Path = (directory / output_name).with_suffix(
                f".{extension['short_name']}"
            )

            render_scene: str = await thread_maya.execute_in_main_thread(
                cmds.file, q=True, sn=True
            )

            batch_cmd = (
                CommandBuilder("C:/Maya2022/Maya2022/bin/Render.exe", delimiter=None)
                .param("r", "vray")
                .param("rl", layer)
                .param("exportFileName", str(output_path))
                .param("noRender")
            )

            batch_cmd.set_last_param(render_scene)

            await thread_client.execute_in_thread(
                subprocess.call, batch_cmd.as_argv(), shell=True
            )

            output_files.append(output_path)

        return output_files

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
                ].value = "No selection detected -> Please select somthing or publish full scene"
            else:
                self.command_buffer.parameters["info"].type = TextParameterMeta(
                    "warning"
                )
                self.command_buffer.parameters[
                    "info"
                ].value = "Select somthing to publish"

        render_layers: List[str] = await thread_maya.execute_in_main_thread(
            cmds.ls, typ="renderLayer"
        )
        self.command_buffer.parameters[
            "render_layers"
        ].type = MultipleSelectParameterMeta(*render_layers)
