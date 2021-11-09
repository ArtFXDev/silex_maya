from __future__ import annotations
from silex_maya.utils.utils import Utils
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.datatypes import CommandOutput

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
        # TODO: This should be done in the get_value method of the ParameterBuffer
        for value in parameters["values"]:
            if isinstance(value, CommandOutput):
                value = value.get_value(action_query)
            values.append(value)

        # Define the function that will repath all the references
        def set_references(attributes, values):
            new_values = []
            for index, attribute in enumerate(attributes):
                # If the attribute is a maya reference
                if cmds.nodeType(attribute) == "reference":
                    cmds.file(values[index], loadReference=attribute)
                    continue
                # If the attribute if from an other referenced scene
                if cmds.referenceQuery(attribute, isNodeReferenced=True):
                    continue

                # If it is just a file node or a texture...
                cmds.setAttr(attribute, values[index], type="string")
                new_values.append(values[index])

            cmds.filePathEditor(rf=True)
            return new_values

        # Execute the function in the main thread
        new_values = await Utils.wrapped_execute(
            action_query, set_references, parameters["attributes"], values
        )
        return await new_values
