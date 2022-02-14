from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import TaskFileParameterMeta
from silex_maya.utils.thread import execute_in_main_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import pathlib

import maya.cmds as cmds


class Reference(CommandBase):
    """
    Reference another Maya scene into the currently opened scene
    """

    parameters = {
        "reference": {
            "label": "Reference file",
            "type": TaskFileParameterMeta(extensions=[".ma", ".mb"]),
            "hide": False,
        },
        "enable_namespace": {"label": "Enable namespace", "type": bool, "value": True},
        "namespace": {"label": "Namespace", "type": str, "value": ""},
    }

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        self.command_buffer.parameters[
            "namespace"
        ].hide = not self.command_buffer.parameters["enable_namespace"].value

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        reference: pathlib.Path = parameters["reference"]
        file_name = reference.stem

        args: Dict[str, Any] = {"r": True}

        if parameters["enable_namespace"]:
            args["namespace"] = parameters["namespace"] or file_name

        await execute_in_main_thread(cmds.file, str(reference), **args)
