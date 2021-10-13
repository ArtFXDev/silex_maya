from __future__ import annotations
import typing
from typing import Any, Dict

from silex_maya.utils.utils import Utils
from silex_client.action.command_base import CommandBase
from silex_client.core.context import Context
from concurrent import futures
# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.dialogs import Dialogs

import os
import gazu.files
import gazu.task
import maya.cmds as cmds

class Build(CommandBase):
    """
    Save current scene with context as path
    """

    parameters = {
        "filename": { "label": "filename", "type": str, "value": "", "hide": True }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        
        async def get_scene_path():
            print(action_query.context_metadata)
            task = await gazu.task.get_task(action_query.context_metadata.get("task_id", ""))
            working_files = await gazu.files.build_working_file_path(task["id"])
            soft = await gazu.files.get_software_by_name("maya")
            working_files += soft.get("file_extension", ".no")
            return working_files
            
        def build():
            future = Context.get().event_loop.register_task(get_scene_path())

            # create recusively directory from path
            working_files = future.result()
            working_folders = os.path.dirname(working_files)
            
            # if file already exist
            if os.path.isfile(working_files):
                Dialogs().inform("File already Exists")
                return

            os.makedirs(working_folders)
            cmds.file(rename = working_files)
            cmds.file(save = True)
        await Utils.wrapped_execute(action_query, build)
