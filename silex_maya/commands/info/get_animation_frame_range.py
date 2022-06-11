from __future__ import annotations

import logging
import typing
from typing import Any, Dict

import maya.cmds as cmds
from silex_client.action.command_base import CommandBase
from silex_maya.utils.thread import execute_in_main_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class GetAnimationFrameRange(CommandBase):
    """
    Return the animation and timeline frame range as a FrameSet string
    """

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        playback_start = await execute_in_main_thread(
            cmds.playbackOptions, q=True, min=True
        )
        playback_end = await execute_in_main_thread(
            cmds.playbackOptions, q=True, max=True
        )

        animation_start = await execute_in_main_thread(
            cmds.playbackOptions, q=True, animationStartTime=True
        )
        animation_end = await execute_in_main_thread(
            cmds.playbackOptions, q=True, animationEndTime=True
        )

        playback = f"{int(playback_start)}-{int(playback_end)}x1"
        animation = f"{int(animation_start)}-{int(animation_end)}x1"

        return {
            "playback": playback,
            "animation": animation,
        }
