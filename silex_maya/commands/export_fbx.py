from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import IntArrayParameterMeta, TextParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.utils import Utils

import maya.cmds as cmds
import os
import pathlib
import gazu
import logging

class ExportFBX(CommandBase):
    """
    Export selection as FBX
    """

    parameters = {
        "file_dir": {
            "label": "File directory",
            "type": pathlib.Path,
            "value": None,
        },
        "file_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": None,
        },
        "root_name": {"label": "Out Object Name", "type": str, "value": "" },
         "timeline_as_framerange": {
            "label": "Take timeline as frame-range?",
            "type": bool,
            "value": False,
            "hide": False,
        },
        "frame_range": {
            "label": "Frame Range",
            "type": IntArrayParameterMeta(2),
            "value": [0, 0],
        },
    }

    async def _prompt_info_parameter(self, action_query: ActionQuery, message: str, level: str = "warning") -> pathlib.Path:
        """
        Helper to prompt the user a label
        """
        # Create a new parameter to prompt label

        info_parameter = ParameterBuffer(
            type=TextParameterMeta(level),
            name="Info",
            label="Info",
            value= f"Warning : {message}",
        )
        # Prompt the user with a label
        prompt = await self.prompt_user(action_query, {"info": info_parameter})

        return prompt["info"]

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.logger
    ):
        # get selected objects
        def selected_objects():
            # get current selection 
            selected = cmds.ls(sl=True,long=True) or []
            selected.sort(key=len, reverse=True) # reverse
            return selected
        # get select objects
        def export_fbx(export_path, object_list, used_timeline, start_frame, end_frame):
            if used_timeline:
                start_frame = cmds.playbackOptions(q=True, animationStartTime=True)
                end_frame = cmds.playbackOptions(q=True, animationEndTime=True)

            cmds.select(object_list)
            cmds.bakeSimulation(object_list) # Needed
            cmds.FBXExportSplitAnimationIntoTakes("-clear")
            cmds.FBXExportSplitAnimationIntoTakes("-v", "Maya_FBX_Export_Take", start_frame, end_frame)
            cmds.FBXExport("-f", export_path, "-s")

        # Get the output path
        directory = parameters.get("file_dir")
        file_name = parameters.get("file_name")
        root_name = parameters.get("root_name")
        used_timeline = parameters.get("timeline_as_framerange")
        start_frame = parameters.get("frame_range")[0]
        end_frame = parameters.get("frame_range")[1]

        # authorized type
        authorized_types = ["transform", "mesh", "camera"]        

        # get selected object
        selected = await Utils.wrapped_execute(action_query, lambda: selected_objects())
        selected = await selected # because first 'selected' is futur
        
        # exclude unauthorized type       
        selected = [item for item in selected if cmds.objectType(item.split("|")[-1]) in authorized_types]

        while len(selected) == 0:
            await self._prompt_info_parameter(action_query, "Could not export the selection: No selection detected")
            selected = await Utils.wrapped_execute(action_query, lambda: selected_objects())
            selected = await selected # because first 'selected' is futur
            selected = [item for item in selected if cmds.objectType(item.split("|")[-1]) in authorized_types]
        
        # Export the selection in OBJ
        os.makedirs(directory, exist_ok=True)

        # compute path
        export_path = directory / f"{file_name}_{root_name}" if root_name else directory / f"{file_name}"
        extension = await gazu.files.get_output_type_by_name("fbx")
        export_path = export_path.with_suffix(f".{extension['short_name']}")

        # Export obj to fbx
        await Utils.wrapped_execute(action_query, export_fbx, export_path, selected, used_timeline, start_frame, end_frame)

        return str(export_path)

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        self.command_buffer.parameters["frame_range"].hide = parameters.get("timeline_as_framerange")
        pass