from __future__ import annotations
import asyncio
import typing
import logging 
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
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        # Create the selected node
        cube_future = await Utils.wrapped_execute(action_query, cmds.polyCube)
        await asyncio.sleep(0.2)
        return await cube_future

    @CommandBase.conform_command()
    async def undo(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        # Create the selected node
        await Utils.wrapped_execute(
            action_query, cmds.delete, self.command_buffer.output_result[0]
        )
        await asyncio.sleep(0.2)
