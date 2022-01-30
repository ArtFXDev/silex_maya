from __future__ import annotations

import logging
import os
import pathlib
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import (
    IntArrayParameterMeta,
    MultipleSelectParameterMeta,
)
from silex_maya.utils.thread import execute_in_main_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import gazu
import gazu.files
from maya import cmds


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
        "selection": {
            "label": "Export selection",
            "type": bool,
            "value": True,
        },
        "options": {
            "label": "Options",
            "type": MultipleSelectParameterMeta(
                **{
                    "Write Visibility": "-wv",
                    "World Space": "-ws",
                    "UV Write": "-uv",
                    "UV Sets Write": "-wuvs",
                    "Write Creases": "-wc",
                    "Strip Namespaces": "-sn",
                    "Write Visibility": "-wv",
                }
            ),
            "value": [],
        },
    }

    def export_abc(
        self, start: int, end: int, path: str, roots: List[str], options: List[str]
    ) -> str:
        """
        Build and execute the abc command with the given options
        """
        joined_roots = "-root " + " -root ".join(roots)
        cmd = (
            f"-dataFormat ogawa {joined_roots if roots else ''} -frameRange {start} {end} -file {path} "
            + " ".join(options)
        )
        cmds.AbcExport(j=cmd)
        return cmd

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Get the output path and range variable
        directory: pathlib.Path = parameters["directory"]
        file_name: pathlib.Path = parameters["file_name"]
        start_frame: int = parameters["frame_range"][0]
        end_frame: int = parameters["frame_range"][1]
        is_timeline: bool = parameters["timeline_as_framerange"]
        selection: bool = parameters["selection"]
        options: List[str] = parameters["options"]

        # Set frame range
        if is_timeline:
            start_frame: int = cmds.playbackOptions(minTime=True, query=True)
            end_frame: int = cmds.playbackOptions(maxTime=True, query=True)

        # Create temps directory
        os.makedirs(directory, exist_ok=True)

        # Compute path
        extension: dict = await gazu.files.get_output_type_by_name("abc")
        export_path: pathlib.Path = (directory / f"{file_name}").with_suffix(
            f".{extension['short_name']}"
        )

        roots = []
        if selection:
            roots = await execute_in_main_thread(cmds.ls, sl=True, l=True)

        # Export in alembic
        cmd = await execute_in_main_thread(
            self.export_abc, start_frame, end_frame, export_path, roots, options
        )
        logger.info("Exported Alembic with command %s", cmd)

        return export_path

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        self.command_buffer.parameters["frame_range"].hide = parameters.get(
            "timeline_as_framerange", False
        )
