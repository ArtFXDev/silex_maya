from __future__ import annotations

import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase

from silex_maya.utils import utils

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

        logger.info(f"Load: {plugin_name}")
        await utils.wrapped_execute(action_query, load_plugin, plugin_name)
