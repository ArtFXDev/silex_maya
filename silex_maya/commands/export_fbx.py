from __future__ import annotations

import typing
from concurrent.futures import Future
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import IntArrayParameterMeta, TextParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import logging
import os
import pathlib

import gazu
import gazu.files
from maya import cmds

from silex_maya.utils import utils


class ExportFBX(CommandBase):
    """
    Export selection as FBX
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
        "root_name": {"label": "Out Object Name", "type": str, "value": ""},
        "timeline_as_framerange": {
            "label": "Take timeline as frame-range?",
            "type": bool,
            "value": False,
        },
        "frame_range": {
            "label": "Frame Range",
            "type": IntArrayParameterMeta(2),
            "value": [0, 0],
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

    # get selected objects
    def selected_objects(self) -> List[str]:
        """Get selection in open scene"""

        # Authorized type
        authorized_types: List[str] = ["transform", "mesh", "camera"]

        # Get current selection
        selected = cmds.ls(sl=True, long=True) or []
        selected.sort(key=len, reverse=True)  # reverse
        selected = [
            item for item in selected if cmds.objectType(item) in authorized_types
        ]

        return selected

    # Get select objects
    def export_fbx(
        self, export_path, object_list, used_timeline, start_frame, end_frame
    ):
        """Export in fbx format"""
        if used_timeline:
            start_frame = cmds.playbackOptions(q=True, animationStartTime=True)
            end_frame = cmds.playbackOptions(q=True, animationEndTime=True)

        cmds.select(object_list)
        cmds.bakeResults(object_list)  # Needed
        cmds.FBXExportSplitAnimationIntoTakes("-clear")
        cmds.FBXExportSplitAnimationIntoTakes(
            "-v", "Maya_FBX_Export_Take", start_frame, end_frame
        )
        cmds.FBXExport("-f", export_path, "-s")

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        # Get the output path
        directory: pathlib.Path = parameters[
            "directory"
        ]  # directory parameter is temp directory
        file_name: pathlib.Path = parameters["file_name"]
        root_name: str = parameters["root_name"]
        used_timeline: bool = parameters["timeline_as_framerange"]
        start_frame: int = parameters["frame_range"][0]
        end_frame: int = parameters["frame_range"][1]

        # Get selected object
        selected: Future = await utils.wrapped_execute(
            action_query, self.selected_objects
        )
        selected: List[str] = await selected

        while len(selected) == 0:
            await self._prompt_info_parameter(
                action_query, "Could not export the selection: No selection detected"
            )
            selected = await utils.wrapped_execute(action_query, self.selected_objects)

        # create temps directory
        os.makedirs(directory, exist_ok=True)

        # Compute path
        export_path = (
            directory / f"{file_name}_{root_name}"
            if root_name
            else directory / f"{file_name}"
        )
        extension = await gazu.files.get_output_type_by_name("fbx")
        export_path = export_path.with_suffix(f".{extension['short_name']}")

        # Export obj to fbx
        await utils.wrapped_execute(
            action_query,
            self.export_fbx,
            export_path,
            selected,
            used_timeline,
            start_frame,
            end_frame,
        )

        return export_path

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        self.command_buffer.parameters["frame_range"].hide = parameters.get(
            "timeline_as_framerange"
        )
        pass
