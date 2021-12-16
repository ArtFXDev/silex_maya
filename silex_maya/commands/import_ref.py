
from __future__ import annotations
from os import name
import typing

from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import TextParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
    
from silex_maya.utils.utils import Utils

import pathlib
import maya.cmds as cmds
import logging

class ImportRef(CommandBase):
    """
    Export selection as FBX
    """

    parameters = {
        "file_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": None,
        },
        "namespace": {"label": "Custom namespace name", "type": str, "value": None }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.logger
    ):
        
        def import_ref(scene_path, namespace):
            # import maya command
            cmds.file(scene_path, reference=True, namespace=namespace)

        file_name: pathlib.Path = parameters.get("file_name")
        namespace = parameters.get("namespace")
        if not namespace:
            namespace = file_name.name

        await Utils.wrapped_execute(action_query, import_ref, file_name, namespace)
        return file_name