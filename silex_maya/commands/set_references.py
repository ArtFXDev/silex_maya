from __future__ import annotations
import logging
import pathlib
import re
import typing
from typing import Any, Dict, List, Union

import fileseq
from silex_client.action.command_base import CommandBase
from silex_client.utils.files import format_sequence_string
from silex_client.utils.parameter_types import AnyParameter, ListParameterMeta

from maya import cmds
from silex_maya.utils.thread import execute_in_main_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


# Some references are actually read only, and set from an other attribute
ATTRIBUTE_MAPPING = {
    "VRayVolumeGrid": {
        "inPathResolved": "inPath",
    }
}


class SetReferences(CommandBase):
    """
    Repath the given references
        "inPathResolved": "inPath","""

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

    def _get_attribute(self, attribute: str):
        """
        Maya has some readonly attribute that are set by and other attribute

        If that's the case, we need to find the setter attribute using the
        ATTRIBUTE_MAPPING mapping
        """
        node_type = cmds.nodeType(attribute)
        attribute_split = attribute.split(".")

        if len(attribute_split) <= 1:
            return attribute

        attrib_name = attribute_split[-1]
        node_name = attribute_split[0]

        attrib_name = (
            ATTRIBUTE_MAPPING.get(node_type, {}).get(attrib_name) or attrib_name
        )
        return ".".join([node_name, attrib_name])

    def _set_reference(self, attribute: str, value: Union[fileseq.FileSequence]) -> str:
        """
        Set the given reference to the given value, after checking the type of reference
        This handles the case of file sequences syntac like #### or <frame01>
        """
        # Get the real value to set
        reference_value = str(pathlib.Path(str(value)))
        if isinstance(value, fileseq.FileSequence):
            previous_value = cmds.getAttr(attribute)
            REGEX_MATCH = [
                re.compile(r"^.+\W(\<.+\>)\W.+$"),  # Matches V-ray's <Whatever> syntax
                re.compile(r"^.+[^\w#](#+)\W.+$"),  # Matches V-ray's ####  syntax
            ]
            reference_value = format_sequence_string(value, previous_value, REGEX_MATCH)

        # If the attribute is a maya reference
        if cmds.nodeType(attribute) == "reference":
            cmds.file(reference_value, loadReference=attribute)
            return reference_value
        # If the attribute is from an other referenced scene
        if cmds.referenceQuery(attribute, isNodeReferenced=True):
            return ""

        # If it is just a file node or a texture...
        split_attributes = attribute.split(".")

        base_node = split_attributes[0]
        colorspace_attribute = ""
        colorspace_value = ""
        if cmds.attributeQuery("colorSpace", node=attribute, exists=True):
            colorspace_attribute = f"{base_node}.colorSpace"
            colorspace_value = cmds.getAttr(colorspace_attribute)

        # File node
        cmds.setAttr(attribute, reference_value, type="string")
        if cmds.attributeQuery("colorSpace", node=attribute, exists=True):
            cmds.setAttr(colorspace_attribute, colorspace_value, type="string")

        return reference_value

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        attributes: List[str] = parameters["attributes"]
        values = []
        # TODO: This should be done in the get_value method of the ParameterBuffer
        for value in parameters["values"]:
            value = value.get_value(action_query)[0]
            value = value.get_value(action_query)
            values.append(value)

        # Execute the function in the main thread
        new_values = []
        for attribute, value in zip(attributes, values):
            if isinstance(value, list):
                value = fileseq.findSequencesInList(value)[0]

            attribute = await execute_in_main_thread(self._get_attribute, attribute)
            new_value = await execute_in_main_thread(
                self._set_reference, attribute, value
            )
            logger.info("Attribute %s set to %s", attribute, value)
            new_values.append(new_value)

        return new_values
