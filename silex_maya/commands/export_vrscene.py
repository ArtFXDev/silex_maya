from __future__ import annotations

import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder
from silex_client.utils import thread as thread_client
from silex_client.utils.parameter_types import MultipleSelectParameterMeta, TextParameterMeta
from silex_client.action.parameter_buffer import ParameterBuffer

from silex_maya.utils import thread as thread_maya

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import logging
import pathlib
import subprocess
import os

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
            "value": ["defaultRenderLayer"],
        },
    }

    async def _prompt_error(self, action_query: ActionQuery) -> bool:
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
                value="Vrscene was not exported. Try to manualy reload Vrayformaya plugins (turn auto-load on and restart maya)"
            )

            # Prompt the user with a label
            await self.prompt_user(
                action_query, {"info": info_parameter}
            )

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

        # Batch: Export vrscene for each render layer
        output_files: List[pathlib.Path] = list()
        command_label = self.command_buffer.label

        render_scene: str = await thread_maya.execute_in_main_thread(cmds.file, q=True, sn=True)

        for index, layer in enumerate(render_layers):

            # Diplay feed back in front
            new_label = f"{command_label}: ({index + 1}/{len(render_layers)}) --> Exporting: {layer}"
            self.command_buffer.label = new_label
            await action_query.async_update_websocket(apply_response=False)

            # the Output filename depends on the layer
            output_name: pathlib.Path = pathlib.Path(f"{file_name}_{layer}")
            output_path: pathlib.Path = (directory / output_name).with_suffix(
                f".{extension['short_name']}"
            )

            batch_cmd = (
                command_builder.CommandBuilder(
                    "C:/Maya2022/Maya2022/bin/Render.exe", delimiter=None
                )
                .param("r", "vray")
                .param("rl", layer)
                .param("exportFileName", str(output_path))
                .param("noRender")
                .value(str(render_scene))
            )

            await thread_client.execute_in_thread(
                subprocess.call, batch_cmd.as_argv(), shell=True
            )

            output_files.append(output_path)

            # Check output
            if not os.path.exists(output_path):
                await self._prompt_error(action_query)

        return output_files

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        # Warning message
        render_layers: List[str] = await thread_maya.execute_in_main_thread(
            cmds.ls, typ="renderLayer"
        )

        self.command_buffer.parameters[
            "render_layers"
        ].type = MultipleSelectParameterMeta(*render_layers)