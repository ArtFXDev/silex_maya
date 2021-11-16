from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import IntArrayParameterMeta
from silex_client.utils.log import logger


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.utils import Utils

import maya.cmds as cmds
import os
import pathlib
import gazu


class ExportABC(CommandBase):
    """
    Export selection as abc
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
        "timeline_as_framerange": { "label": "Take timeline as frame-range?", "type": bool, "value": False },
        "frame_range": {
            "label": "Frame Range",
            "type": IntArrayParameterMeta(2),
            "value": [0, 0]
        }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        
        # get select objects
        def select_objects():
            # get current selection 
            selected = cmds.ls(sl=True,long=True) or []
            selected.sort(key=len, reverse=True) # reverse
            return selected

        # export abc method for wrapped execute
        def export_abc(start: int, end: int, path: str, obj):
            # Check selected root
            if obj is None:
                raise Exception("ERROR: No root found")
            logger.info(f"export : {obj}")

            cmds.AbcExport(j=f"-uvWrite -dataFormat ogawa -root {obj} -frameRange {start} {end} -file {path}")

        # Get the output path and range variable
        directory = parameters.get("file_dir")
        file_name = parameters.get("file_name")
        start_frame = parameters.get("frame_range")[0]
        end_frame = parameters.get("frame_range")[1]
        used_timeline = parameters.get("timeline_as_framerange")

        # authorized type
        authorized_type = ["transform", "mesh", "camera"]
        
        # list of path to return
        to_return_paths = []

        # Set frame range
        if used_timeline:
            start_frame = cmds.playbackOptions(minTime=True, query=True)
            end_frame = cmds.playbackOptions(maxTime=True, query=True)
        
        # get selected objects
        selected = await Utils.wrapped_execute(action_query, lambda: select_objects())
        selected = await selected

        # create abc dir
        os.makedirs(directory, exist_ok=True)
        
        for obj in selected:
            name = obj.split("|")[-1]
            type = cmds.objectType(name)
            if type not in authorized_type:
                continue

            # compute path
            export_path = directory / f"{file_name}_{name}"
            extension = await gazu.files.get_output_type_by_name("abc")
            export_path = export_path.with_suffix(f".{extension['short_name']}")

            # add path to return list
            to_return_paths.append(str(export_path))
            
            await Utils.wrapped_execute(
                action_query, lambda: export_abc(start_frame, end_frame, export_path, name)
            )

        return to_return_paths
