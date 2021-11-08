from __future__ import annotations
from silex_maya.utils.utils import Utils
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger
from silex_client.utils.datatypes import CommandOutput

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import maya.cmds as cmds


class SetAttributes(CommandBase):
    """
    Set the attribute on given list of attributes
    """

    parameters = {
        "attributes": {
            "label": "Attributes",
            "type": list,
            "value": None,
        },
        "values": {
            "label": "Values",
            "type": list,
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        values = []
        for value in parameters["values"]:
            if isinstance(value, CommandOutput):
                value = value.get_value(action_query)
            values.append(value)

        def set_attribute(attributes, values):
            new_values = []
            for index, attribute in enumerate(attributes):
                cmds.setAttr(attribute, values[index], type="string")
                new_values.append(values[index])

            cmds.filePathEditor(rf=True)
            return new_values

        new_values = await Utils.wrapped_execute(
            action_query, set_attribute, parameters["attributes"], values
        )
        return await new_values
