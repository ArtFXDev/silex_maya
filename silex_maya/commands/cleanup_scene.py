from __future__ import annotations

import typing
import logging
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_maya.utils import utils

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from maya import cmds


class CleanupScene(CommandBase):
    """
    Find all the referenced files, including textures, scene references...
    """

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        def cleanup():
            # Clean unknown nodes
            unknown_nodes = cmds.ls(type="unknown")

            for unknown_node in unknown_nodes:
                cmds.lockNode(unknown_node, lock=False)
                cmds.delete(unknown_node)

        await utils.wrapped_execute(action_query, cleanup)
