from __future__ import annotations
import typing
from typing import Any, Dict

from silex_maya.utils.utils import Utils
from silex_client.action.command_base import CommandBase
from silex_maya.utils.dialogs import Dialogs

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import maya.cmds as cmds

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
        def save():
            # if file already exist
            if not cmds.file(q=True, sn=True):
                Dialogs().warn("Scene not save in pipeline")
                return

            import maya.mel as mel
            mel.eval("incrementAndSaveScene( 0 )")
        

        await Utils.wrapped_execute(action_query, save)
