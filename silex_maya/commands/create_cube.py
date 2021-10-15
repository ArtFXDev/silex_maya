from __future__ import annotations
import asyncio
import typing
from typing import Any, Dict

from maya import cmds

from silex_client.action.command_base import CommandBase
from silex_maya.utils.utils import Utils

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class CreateCube(CommandBase):
    """
    Create the selected node
    """

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        # Create the selected node
        await Utils.wrapped_execute(action_query, cmds.polyCube)
        await asyncio.sleep(0.1)
