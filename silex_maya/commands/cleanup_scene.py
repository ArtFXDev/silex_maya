from __future__ import annotations

import logging
import re
import textwrap
import typing
from typing import Any, Dict, List

from contextlib import suppress
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import TextParameterMeta
from silex_maya.utils.scene import rename_duplicates_nodes
from silex_maya.utils.thread import execute_in_main_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from maya import cmds, mel


class CleanupScene(CommandBase):
    """
    Find all the referenced files, including textures, scene references...
    """

    async def _prompt_fix(self, action_query: ActionQuery, message: str) -> bool:
        """
        Helper to prompt the user if he wants to fix the issue
        """
        # Create a new parameter to prompt for the new file path
        info_parameter = ParameterBuffer(
            type=TextParameterMeta("warning"),
            name="info",
            label=f"Info",
            value=message,
        )
        fix_parameter = ParameterBuffer(
            type=bool,
            name="fix",
            label=f"Do you want to auto fix this issue ?",
            value=False,
        )
        # Prompt the user
        response = await self.prompt_user(
            action_query,
            {
                "info": info_parameter,
                "fix": fix_parameter,
            },
        )
        return response["fix"]

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        def clear_unknown_nodes(unknown_node: List[str]):
            for unknown_node in unknown_nodes:
                # Removing a node can remove others in chain
                # We must check if it was not already deleted
                if not cmds.objExists(unknown_node):
                    continue
                cmds.lockNode(unknown_node, lock=False)
                cmds.delete(unknown_node)

        # Clean unknown nodes
        unknown_nodes = await execute_in_main_thread(cmds.ls, type="unknown")
        if unknown_nodes:
            message = f"""
            The current maya scene contains unknown nodes: 
            {unknown_nodes}

            This might be caused by a plugin that is not accessible on this computer
            """
            if await self._prompt_fix(action_query, textwrap.dedent(message)):
                await execute_in_main_thread(clear_unknown_nodes, unknown_nodes)

        # Rename duplicate names of reference nodes
        reference_nodes = await execute_in_main_thread(
            cmds.filePathEditor, q=True, lf="", ao=True
        )
        regex_filters = [
            re.compile(f"^.+{node.split('.')[0]}(?=\\||$)")
            for node in reference_nodes or []
        ]
        nodes = await execute_in_main_thread(cmds.ls)
        duplicate_nodes = [node for node in nodes if "|" in node]
        regex_search = [
            regex.search(name) for regex in regex_filters for name in duplicate_nodes
        ]
        if any(regex_search):
            message = f"""
            The current maya scene contains reference nodes that have duplicate names:
            {[regex.string for regex in regex_search if regex is not None]}

            Due to an error in maya's file path editor this can cause errors in the conform
            """
            if await self._prompt_fix(action_query, textwrap.dedent(message)):
                await execute_in_main_thread(rename_duplicates_nodes, regex_filters)

        # Remove the vray crop region to prevent rendering region on the renderfarm
        # The exceptions are ignored in case vray is not installed
        with suppress(RuntimeError):
            await execute_in_main_thread(mel.eval, "vray vfbControl -setregion reset")
