from __future__ import annotations

import asyncio
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.datatypes import SharedVariable
from silex_client.utils.parameter_types import (
    IntArrayParameterMeta,
    MultipleSelectParameterMeta,
    SelectParameterMeta,
)
from silex_maya.utils.thread import execute_in_main_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import logging
import pathlib

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
        "camera": {
            "label": "Camera",
            "type": SelectParameterMeta(),
        },
        "render_layers": {
            "label": "Select render layers",
            "type": MultipleSelectParameterMeta(),
            "value": ["defaultRenderLayer"],
        },
        "parameter_overrides": {
            "type": bool,
            "label": "Parameter overrides",
            "value": False,
        },
        "frame_range": {
            "label": "Frame range ( start, end )",
            "type": IntArrayParameterMeta(2),
            "value": [0, 200],
            "hide": True,
        },
    }

    async def update_progress(
        self, action_query: ActionQuery, layer_index: SharedVariable, layer_count: int
    ):
        """
        Helper to prompt the user a label
        """

        def get_frame_progression():
            current_frame = cmds.currentTime(q=True)
            start = cmds.getAttr(f"defaultRenderGlobals.startFrame")
            end = cmds.getAttr(f"defaultRenderGlobals.endFrame")
            return (current_frame + start) / end

        while True:
            await asyncio.sleep(0.2)
            layer_progression = await execute_in_main_thread(get_frame_progression)
            self.command_buffer.progress = (
                (layer_index.value + layer_progression) / layer_count
            ) * 100
            await action_query.async_update_websocket(apply_response=False)

    @staticmethod
    def _load_vray():
        # Ensure plugins are loaded
        cmds.loadPlugin("vrayformaya", quiet=True)
        cmds.loadPlugin("vrayvolumegrid", quiet=True)

        # Auto load
        cmds.pluginInfo("vrayformaya", edit=True, autoload=True)
        cmds.pluginInfo("vrayvolumegrid", edit=True, autoload=True)

        # Edit attribs
        cmds.setAttr("defaultRenderGlobals.currentRenderer", l=False)
        cmds.setAttr("defaultRenderGlobals.currentRenderer", "vray", type="string")

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        directory: pathlib.Path = parameters["directory"]
        file_name: pathlib.Path = parameters["file_name"]
        camera: str = parameters["camera"]
        render_layers: List[str] = parameters["render_layers"]
        extension = await gazu.files.get_output_type_by_name("vrscene")
        parameter_overrides: bool = parameters["parameter_overrides"]
        frame_range: List[int] = parameters["frame_range"]

        # Batch: Export vrscene for each render layer
        command_label = self.command_buffer.label

        await execute_in_main_thread(self._load_vray)
        await execute_in_main_thread(cmds.setAttr, "vraySettings.vrscene_render_on", 0)
        await execute_in_main_thread(cmds.setAttr, "vraySettings.vrscene_on", 1)
        if parameter_overrides:
            await execute_in_main_thread(
                cmds.setAttr, "defaultRenderGlobals.startFrame", frame_range[0]
            )
            await execute_in_main_thread(
                cmds.setAttr, "defaultRenderGlobals.endFrame", frame_range[1]
            )

        layer_index = SharedVariable(0)
        task = asyncio.create_task(
            self.update_progress(action_query, layer_index, len(render_layers))
        )
        for index, layer in enumerate(render_layers):
            # Diplay feed back in front
            new_label = f"{command_label}: ({index + 1}/{len(render_layers)}) --> Exporting: {layer}"
            self.command_buffer.label = new_label
            layer_index.value = index
            self.command_buffer.progress = (index / len(render_layers)) * 100
            await action_query.async_update_websocket(apply_response=False)

            # The Output filename depends on the layer
            output_name: pathlib.Path = pathlib.Path(f"{file_name}_{layer}")
            output_path: pathlib.Path = (directory / output_name).with_suffix(
                f".{extension['short_name']}"
            )

            await execute_in_main_thread(
                cmds.setAttr,
                "vraySettings.vrscene_filename",
                output_path,
                type="string",
            )
            await execute_in_main_thread(
                cmds.editRenderLayerGlobals, currentRenderLayer=layer
            )
            logger.info("Executing: vrend on layer %s to %s", layer, output_path)
            await execute_in_main_thread(cmds.setAttr, f"{camera}.renderable", 1)
            await execute_in_main_thread(cmds.vrend, camera=camera)

        task.cancel()

        if "defaultRenderLayer" in await execute_in_main_thread(
            cmds.ls, type="renderLayer"
        ):
            try:
                await execute_in_main_thread(
                    cmds.editRenderLayerGlobals, currentRenderLayer="defaultRenderLayer"
                )
            except Exception as e:
                logger.error(str(e))

        await execute_in_main_thread(cmds.setAttr, "vraySettings.vrscene_render_on", 1)
        await execute_in_main_thread(cmds.setAttr, "vraySettings.vrscene_on", 0)

        return directory

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        # Warning message
        render_layers: List[str] = await execute_in_main_thread(
            cmds.ls, typ="renderLayer"
        )

        self.command_buffer.parameters[
            "render_layers"
        ].type = MultipleSelectParameterMeta(*render_layers)

        # Overriding frame_range is optional
        hide_overrides = not parameters["parameter_overrides"]
        self.command_buffer.parameters["frame_range"].hide = hide_overrides

        # Fill the list of possible cameras
        renderable_cameras = await execute_in_main_thread(cmds.ls, type="camera")
        self.command_buffer.parameters["camera"].rebuild_type(*renderable_cameras)
