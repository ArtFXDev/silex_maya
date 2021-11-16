from __future__ import annotations
from silex_maya.utils.utils import Utils
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_types import ListParameterMeta
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import maya.cmds as cmds


class SetReferences(CommandBase):
    """
    Repath the given references
    """

    parameters = {
        "attributes": {
            "label": "Attributes",
            "type": ListParameterMeta(str),
            "value": None,
        },
        "values": {
            "label": "Values",
            "type": ListParameterMeta(str),
            "value": None,
        },
        "indexes": {
            "label": "Indexes",
            "type": ListParameterMeta(int),
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        attributes: List[str] = parameters["attributes"]
        indexes: List[str] = parameters["indexes"]

        values = []
        # TODO: This should be done in the get_value method of the ParameterBuffer
        for value in parameters["values"]:
            value = value.get_value(action_query)[0]
            value = value.get_value(action_query)
            values.append(value)

        # Define the function that will repath all the references
        def set_reference(attribute, value):
            # If the attribute is a maya reference
            if cmds.nodeType(attribute) == "reference":
                cmds.file(value, loadReference=attribute)
                return value
            # If the attribute if from an other referenced scene
            if cmds.referenceQuery(attribute, isNodeReferenced=True):
                return ""

            # If it is just a file node or a texture...
            cmds.setAttr(attribute, value, type="string")
            return value

        # Execute the function in the main thread
        new_values = []
        for attribute, index, value in zip(attributes, indexes, values):
            value = value[index]
            new_value = await Utils.wrapped_execute(
                action_query, set_reference, attribute, value
            )
            logger.info("Attribute %s set to %s", attribute, value)
            new_values.append(await new_value)

        return new_values