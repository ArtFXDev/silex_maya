from __future__ import annotations
import typing
from typing import Any, Dict

from silex_maya.utils.utils import Utils
from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.dialogs import Dialogs

import asyncio
import os
import gazu.files
import gazu.task
import maya.cmds as cmds
import maya.mel as mel
import re


class Save(CommandBase):
    """
    Save current scene with context as path
    """

    parameters = {
        "filename": {"label": "filename", "type": str, "value": "", "hide": True}
    }
    required_metadata = ['task_id']

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        async def get_scene_path():
            # task = await gazu.task.get_task(action_query.context_metadata.get("task_id", "ac0e79cf-e5ce-49ff-932f-6aed3d425e4a"))
            task_id: str = action_query.context_metadata.get("task_id", "none")
            working_file_with_extension = await gazu.files.build_working_file_path(task_id)
            if task_id == "none":
                Dialogs().err("Invalid task_id !")
                return -1, None

            soft = await gazu.files.get_software_by_name("maya")
            extension = soft.get("file_extension", ".no")
            extension = extension if '.' in extension else f".{extension}"
            working_file_with_extension += extension
            if extension == ".no":
                Dialogs().warn("Sofware not set in Kitsu, file extension will be invalid")
                return -1, None

            return working_file_with_extension, extension

        def save():

            # create recusively directory from path
            working_file_with_extension, ext = asyncio.run(get_scene_path())

            # error in future
            if working_file_with_extension == -1 or not ext:
                return

            filename = os.path.basename(working_file_with_extension)
            working_file_without_extension = os.path.splitext(filename)[0]
            working_folders = os.path.dirname(working_file_with_extension)

            # if file already exist
            version = re.findall("[0-9]*$", working_file_without_extension)
            # get last number of file name
            version = version[0] if len(version) > 0 else ""
            zf = len(version)
            version = int(version)

            # error in future
            if version == "":
                Dialogs().err("Failed to get version from regex")
                return

            file_without_version = re.findall(
                "(?![0-9]*$).", working_file_without_extension)
            file_without_version = ''.join(file_without_version)
            while os.path.exists(working_file_with_extension):
                version += 1
                working_file_with_extension = os.path.join(
                    working_folders, f"{file_without_version}{str(version).zfill(zf)}{ext}")

            if not os.path.exists(working_folders):
                os.makedirs(working_folders)

            cmds.file(rename=working_file_with_extension)
            cmds.file(save=True)
        await Utils.wrapped_execute(action_query, save)
