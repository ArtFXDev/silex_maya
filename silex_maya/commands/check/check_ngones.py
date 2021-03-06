from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from maya import cmds
from silex_client.action.command_base import CommandBase
from silex_maya.utils.thread import execute_in_main_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class CheckNgones(CommandBase):
    """
    check for N-gones in scene
    """

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        def check_ngons():
            logger.info("check ngones")

            # Select all dag objects
            cmds.select(ado=True)

            # Filter selection to N-gones
            cmds.polySelectConstraint(m=3, t=8, sz=3)

            sel_size: int = len(cmds.ls(sl=True))

            if sel_size:
                # restore selection constraint
                cmds.polySelectConstraint(m=3, t=8, sz=2)
                cmds.select(clear=True)

                raise Exception(f"{sel_size} N-gones found")

        await execute_in_main_thread(lambda: check_ngons())
