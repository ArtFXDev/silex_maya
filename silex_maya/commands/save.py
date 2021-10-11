from __future__ import annotations
import typing
from typing import Any, Dict

import os

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

#import maya.cmds as cmds

class Save(CommandBase):
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
        print("aaa")
        print(action_query.context_metadata)
        print([action_query.context_metadata.get("project", ""), action_query.context_metadata.get("sequence", ""), action_query.context_metadata.get("shot", ""), action_query.context_metadata.get("task", ""), "work"])
        meta = action_query.context_metadata
        print([meta.get("project", ""), meta.get("sequence", ""), meta.get("shot", ""), meta.get("task", ""), "work"])
        print(os.path.join("work", meta.get("sequence", "")))
        final_path = os.path.join(meta.get("project", ""), meta.get("sequence", ""), meta.get("shot", ""), meta.get("task", ""), "work")
        print(final_path)
        
        #cmds.file(rename = path[0])
        #cmds.file(save = True)
