from __future__ import annotations

import os
import fileseq
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

    async def _prompt_new_path(
        self, action_query: ActionQuery, old_path: pathlib.Path
    ) -> pathlib.Path:
        """
        Helper to prompt the user for a new path and wait for its response
        """
        # Create a new parameter to prompt for the new file path
        new_parameter = ParameterBuffer(
            type=pathlib.Path,
            name="new_path",
            label=f"The file {old_path} is not reachable, insert an other path",
        )
        # Prompt the user to get the new path
        file_path = await self.prompt_user(
            action_query,
            {"new_path": new_parameter},
        )
        return pathlib.Path(file_path["new_path"])

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        # Define the function to get all the referenced files in the scene
        def get_referenced_files():
            cmds.filePathEditor(rf=True)
            referenced_files = []

            # Get the referenced files from the file path editor
            for attribute in cmds.filePathEditor(q=True, lf="", ao=True) or []:
                # Skip the nodes that are from an other referenced scene
                if cmds.referenceQuery(attribute, isNodeReferenced=True):
                    continue
                # If the attribute is a maya/alembic/... reference
                if cmds.nodeType(attribute) == "reference":
                    file_path = cmds.referenceQuery(attribute, filename=True)
                    referenced_files.append((attribute, pathlib.Path(file_path)))
                    continue
                # Otherwise, just get the attribute for simple stuff like file nodes
                file_path = cmds.getAttr(attribute)
                referenced_files.append((attribute, pathlib.Path(file_path)))
            return referenced_files

        # Execute the get_referenced_files in the main thread
        referenced_files = await Utils.wrapped_execute(
            action_query, get_referenced_files
        )

        # Each referenced file must be verified
        verified_referenced_files = []

        # Check if the referenced files are reachable and prompt the user if not
        for attribute, file_path in await referenced_files:
            frame_set = fileseq.FrameSet(0)
            # Make sure the file path leads to a reachable file
            while not file_path.exists() or file_path.is_absolute():
                logger.warning(
                    "Could not reach the file %s at %s", file_path, attribute
                )
                file_path = await self._prompt_new_path(action_query, file_path)

            # Look for a file sequence
            for file_sequence in fileseq.findSequencesOnDisk(str(file_path.parent)):
                # Find the file sequence that correspond the to file we are looking for
                sequence_list = [pathlib.Path(str(file)) for file in file_sequence]
                if file_path in sequence_list and len(sequence_list) > 1:
                    frame_set = file_sequence.frameSet()
                    file_path = sequence_list
                    break

            # Append to the verified path
            verified_referenced_files.append((attribute, file_path, frame_set))
            logger.info("Referenced file %s found at %s", file_path, attribute)

        return {
            "attributes": [file[0] for file in verified_referenced_files],
            "file_paths": [file[1] for file in verified_referenced_files],
            "frame_sets": [file[2] for file in verified_referenced_files],
        }
