from __future__ import annotations

import os
import pathlib
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.log import logger
from silex_maya.utils.utils import Utils

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import maya.cmds as cmds


class GetReferences(CommandBase):
    """
    Find all the referenced files, including textures, scene references...
    """

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        def get_referenced_files():
            cmds.filePathEditor(rf=True)
            # Get the referenced files from the file path editor
            attributes = cmds.filePathEditor(
                query=True, listFiles="", attributeOnly=True
            )

            referenced_files = []
            if attributes is None:
                return referenced_files

            for attribute in attributes:
                # If the attribute if from an other referenced scene
                if cmds.referenceQuery(attribute, isNodeReferenced=True):
                    continue
                # If the attribute is a maya/alembic/... reference
                if cmds.nodeType(attribute) == "reference":
                    file_path = cmds.referenceQuery(attribute, filename=True)
                    referenced_files.append((attribute, file_path))
                    continue
                # Otherwise, just get the attribute for simple stuff like file nodes
                file_path = cmds.getAttr(attribute)
                referenced_files.append((attribute, file_path))
            return referenced_files

        referenced_files = await Utils.wrapped_execute(
            action_query, get_referenced_files
        )
        referenced_files = await referenced_files
        # Each referenced file must be verified
        verified_referenced_files = []

        # Check if the referenced files are reachable and prompt the user if not
        for attribute, file_path in referenced_files:
            while not os.path.exists(file_path) or not os.path.isabs(file_path):
                # Create a new parameter to prompt for the new file path
                new_parameter = ParameterBuffer(
                    type=pathlib.Path,
                    name="new_path",
                    label=f"The file {file_path} is not reachable, insert an other path",
                )
                logger.warning(
                    "Could not reach the file %s prompting user...", file_path
                )
                # Prompt the user to get the new path
                file_path = await self.prompt_user(
                    action_query,
                    {"new_path": new_parameter},
                )
                file_path = file_path["new_path"]
            # If the path is correct, append to the verified path
            verified_referenced_files.append((attribute, file_path))
            logger.info("Referenced file %s found at %s", file_path, attribute)

        return {
            "attributes": [file[0] for file in verified_referenced_files],
            "file_paths": [file[1] for file in verified_referenced_files],
        }
