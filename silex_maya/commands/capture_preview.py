from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_maya.utils.utils import Utils
from silex_maya.utils.preview import create_thumbnail

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class CapturePreview(CommandBase):
    """
    Capture the current viewport either as a playblast or a single frame
    """

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        # Take a thumbnail of the current viewport
        thumbnail_future = await Utils.wrapped_execute(action_query, create_thumbnail)
        thumbnail = await thumbnail_future

        return thumbnail
