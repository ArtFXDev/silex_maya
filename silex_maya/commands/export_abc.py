from __future__ import annotations
import typing
from typing import Any, Dict
import logging

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import IntArrayParameterMeta


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils import utils

from maya import cmds
import gazu.files
import os
import pathlib
import gazu


class ExportABC(CommandBase):
    """
    Export selection as abc
    """

    parameters = {
        "directory": {
            "type": pathlib.Path,
            "value": None,
        },
        "file_name": {
            "type": pathlib.Path,
            "value": None,
        },
        "timeline_as_framerange": { "label": "Take timeline as frame-range?", "type": bool, "value": False },
        "frame_range": {
            "label": "Frame Range",
            "type": IntArrayParameterMeta(2),
            "value": [0, 0]
        },
        "write_visibility": { "label": "Write Visibility", "type": bool, "value": False },
        "world_space": { "label": "World Space", "type": bool, "value": False },
        "uv_write": { "label": "UV Write", "type": bool, "value": False },
        "write_creases": { "label": "Write Creases", "type": bool, "value": False },
    }

            
    # Get select objects
    def select_objects(self):
        """Get selection in open scene"""

        # Get current selection 
        selected = cmds.ls(sl=True,long=True) or []
        selected.sort(key=len, reverse=True) # reverse
        return selected

    # Export abc method for wrapped execute
    def export_abc(self, start: int, end: int, path: str, obj, write_visibility: bool, world_space: bool, uv_write: bool, write_creases: bool) -> None:
        """Export in alembic"""
        
        # Authorized type
        authorized_type = ["transform", "mesh", "camera"]

        type: str = cmds.objectType(obj)
        if type in authorized_type:

            # Check selected root
            if obj is None:
                raise Exception("ERROR: No root found")
            cmd = f"-dataFormat ogawa {'-uv' if uv_write else ''}"
            cmd.join(f"{'-wv' if write_visibility else ''} {'-ws' if world_space else ''}")
            cmd.join(f"{'-wc' if write_creases else ''} -root {obj} -frameRange {start} {end} -file {path}")
            cmds.AbcExport(j=cmd)


    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        # Get the output path and range variable
        directory: pathlib.Path = parameters["directory"] # Directory is temp directory
        file_name: pathlib.Path = parameters["file_name"]
        start_frame: int = parameters["frame_range"][0]
        end_frame: int = parameters["frame_range"][1]
        is_timeline: bool = parameters["timeline_as_framerange"]
        write_visibility: bool = parameters["write_visibility"]
        world_space: bool = parameters["world_space"]
        uv_write: bool = parameters["uv_write"]
        write_creases: bool = parameters["write_creases"]

        # List of path to return
        to_return_paths = []
        
        # Get selected objects
        selected = await utils.wrapped_execute(action_query, self.select_objects)
        selected = await selected

        # Set frame range
        if is_timeline:
            start_frame: int = cmds.playbackOptions(minTime=True, query=True)
            end_frame: int = cmds.playbackOptions(maxTime=True, query=True)

        # Create temps directory
        os.makedirs(directory, exist_ok=True)
        
        for obj in selected:

            # compute path
            name: str = obj.split("|")[-1]
            extension: str = await gazu.files.get_output_type_by_name('abc')
            export_path: pathlib.Path = (directory / f"{file_name}_{name}").with_suffix(f".{extension['short_name']}")

            # Add path to return list
            to_return_paths.append(str(export_path))
            
            # Export in alambic
            await utils.wrapped_execute(
                action_query,
                self.export_abc,
                start_frame,
                end_frame,
                export_path,
                name,
                write_visibility,
                world_space,
                uv_write,
                write_creases,
            )
            
        return to_return_paths

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        self.command_buffer.parameters["frame_range"].hide = parameters.get("timeline_as_framerange")
