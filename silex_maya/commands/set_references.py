from __future__ import annotations
from silex_maya.utils.utils import Utils
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import ListParameterMeta, AnyParameter
import logging

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
            "type": ListParameterMeta(AnyParameter),
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        attributes: List[str] = parameters["attributes"]
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
            split_attributes = attribute.split(".")
            if len(split_attributes) == 0:
                raise Exception("split_attributes is empty.") # this should never happen

            base_node = split_attributes[0]
            aces_attribute = ""
            aces_value = ""
            if cmds.attributeQuery("colorSpace", node=attribute, exists=True):
                aces_attribute = f"{base_node}.colorSpace"
                aces_value = cmds.getAttr(aces_attribute)

            # file node
            cmds.setAttr(attribute, value, type="string")
            if cmds.attributeQuery("colorSpace", node=attribute, exists=True):
                cmds.setAttr(aces_attribute, aces_value, type="string")

            return value

        # Execute the function in the main thread
        new_values = []
        for attribute, value in zip(attributes, values):
            if isinstance(value, list):
                value = value[-1]

            new_value = await Utils.wrapped_execute(
                action_query, set_reference, attribute, value
            )
            logger.info("Attribute %s set to %s", attribute, value)
            new_values.append(await new_value)

        return new_values
