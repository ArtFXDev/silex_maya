from __future__ import annotations

import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_maya.utils.thread import execute_in_main_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import logging

from maya import cmds


class LoadPlugin(CommandBase):
    """
    Load plugin by name
    """

    parameters = {
        "plugin_name": {
            "label": "Plugin name",
            "type": str,
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        plugin_name = parameters.get("plugin_name")

        def load_plugin(plugin_name):
            cmds.loadPlugin(plugin_name)

            # Ensure autoload 
            cmds.pluginInfo( plugin_name, edit=True, autoload=True )

        logger.info(f"Load: {plugin_name}")
        await execute_in_main_thread(load_plugin, plugin_name)
