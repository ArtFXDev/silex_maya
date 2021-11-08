from __future__ import annotations
from silex_maya.utils.utils import Utils
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import maya.cmds as cmds


class GetReferences(CommandBase):
    """
    Move the maya file and its dependencies into the pipeline file structure
    """

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        def get_referenced_files():
            cmds.filePathEditor(rf=True)
            attributes = cmds.filePathEditor(
                query=True, listFiles="", attributeOnly=True
            )

            referenced_files = []
            if attributes is None:
                return referenced_files

            for attribute in attributes:
                referenced_files.append((attribute, cmds.getAttr(attribute)))
            return referenced_files

        referenced_files = await Utils.wrapped_execute(
            action_query, get_referenced_files
        )
        referenced_files = await referenced_files
        for attribute, file_path in referenced_files:
            logger.info("Referenced file %s found at %s", file_path, attribute)

        return {
            "attributes": [file[0] for file in referenced_files],
            "file_paths": [file[1] for file in referenced_files],
        }
