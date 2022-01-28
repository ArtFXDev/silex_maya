from __future__ import annotations

import distutils.dir_util
import shutil
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import PathParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import logging
import os
import pathlib

import maya.cmds as cmds
import maya.mel as mel
from silex_maya.utils.thread import execute_in_main_thread


class ExportXgen(CommandBase):
    """
    Export a Maya project for XGen
    """

    parameters = {
        "destination": {
            "type": PathParameterMeta(),
            "value": None,
            "hide": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        destination: pathlib.Path = parameters["destination"]

        scene_path = pathlib.Path(
            await execute_in_main_thread(cmds.file, q=True, sn=True)
        )
        scene_folder = os.path.dirname(scene_path)

        xgen_files = [
            scene_path.parents[0] / f
            for f in os.listdir(scene_folder)
            if f.split(".")[-1] == "xgen"
        ]

        # Delete the destination folder
        if os.path.exists(destination):
            shutil.rmtree(destination)
        os.makedirs(destination)

        project_root_dir = pathlib.Path(
            await execute_in_main_thread(cmds.workspace, q=True, rd=True)
        )

        subdirs_to_keep = [
            project_root_dir / p for p in ["xgen", "sourceimages", "workspace.mel"]
        ]

        maya_project_destination = destination / project_root_dir.stem

        # Copy xgen files into the publish
        for xgen_file in xgen_files:
            shutil.copy(xgen_file, destination)

        # Create the target project directory
        os.makedirs(
            maya_project_destination,
            exist_ok=True,
        )

        # Copy the subfolders
        for sub_item in subdirs_to_keep:
            dest_path = maya_project_destination / sub_item.name
            logger.error("Copying %s to %s", sub_item, dest_path)
            if os.path.isdir(sub_item):
                shutil.copytree(sub_item, dest_path)
            else:
                shutil.copy(sub_item, dest_path)
