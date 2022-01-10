from __future__ import annotations

import fileseq
import pathlib
import typing
import logging
from typing import Any, Dict, Tuple, List, Union

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import TextParameterMeta, ListParameterMeta
from silex_client.utils.files import is_valid_pipeline_path, is_valid_path
from silex_maya.utils.utils import Utils

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from maya import cmds
import maya.app.general.fileTexturePathResolver as ftpr


References = List[
    Tuple[
        List[str],
        Union[List[pathlib.Path], pathlib.Path],
    ]
]


class GetReferences(CommandBase):
    """
    Find all the referenced files, including textures, scene references...
    """

    parameters = {
        "skip_conformed": {
            "label": "Skip conformed references",
            "type": bool,
            "value": True,
            "tooltip": "The references that point to a file that is already in the right folder will be skipped",
        },
        "filters": {
            "label": "Custom filters",
            "type": ListParameterMeta(str),
            "value": [],
            "tooltip": "List of file extensions to ignore",
            "hide": True,
        },
    }

    async def _prompt_new_path(
        self, action_query: ActionQuery, file_path: pathlib.Path, parameter: Any
    ) -> Tuple[pathlib.Path, bool, bool]:
        """
        Helper to prompt the user for a new path and wait for its response
        """
        # Create a new parameter to prompt for the new file path
        info_parameter = ParameterBuffer(
            type=TextParameterMeta("warning"),
            name="info",
            label=f"Info",
            value=f"The file:\n{file_path}\n\nReferenced in:\n{parameter}\n\nCould not be reached",
        )
        path_parameter = ParameterBuffer(
            type=pathlib.Path,
            name="new_path",
            label=f"New path",
        )
        skip_all_parameter = ParameterBuffer(
            type=bool,
            name="skip_all",
            value=False,
            label=f"Skip all unresolved reference",
        )
        skip_parameter = ParameterBuffer(
            type=bool,
            name="skip",
            value=False,
            label=f"Skip this reference",
        )
        # Prompt the user to get the new path
        response = await self.prompt_user(
            action_query,
            {
                "info": info_parameter,
                "skip_all": skip_all_parameter,
                "skip": skip_parameter,
                "new_path": path_parameter,
            },
        )
        if response["new_path"] is not None:
            response["new_path"] = pathlib.Path(response["new_path"])
        return response["new_path"], response["skip"], response["skip_all"]

    def _test_possible_sequence(self, attribute: str):
        """
        Define the function to test if an attribute might return a file sequence or not
        """
        # Test the parameters for a file node:
        if cmds.nodeType(attribute) == "file":
            node = ".".join(attribute.split(".")[:-1])
            if cmds.getAttr(f"{node}.uvTilingMode") != 0:
                return True
            if cmds.getAttr(f"{node}.useFrameExtension") == 1:
                return True

        return False

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Define the function to get all the referenced files in the scene
        def get_referenced_files():
            cmds.filePathEditor(rf=True)
            referenced_files: List[Tuple[str, pathlib.Path]] = []

            # Get the referenced files from the file path editor
            for attribute in cmds.filePathEditor(q=True, lf="", ao=True) or []:
                # Skip the nodes that are from an other referenced scene
                if cmds.referenceQuery(attribute, isNodeReferenced=True):
                    continue
                # If the attribute is a maya/alembic/... reference
                if cmds.nodeType(attribute) == "reference":
                    file_path = cmds.referenceQuery(
                        attribute, filename=True, withoutCopyNumber=True
                    )
                    referenced_files.append((attribute, pathlib.Path(file_path)))
                    continue
                # Otherwise, just get the attribute for simple stuff like file nodes
                file_path = cmds.getAttr(attribute)
                referenced_files.append((attribute, pathlib.Path(file_path)))
            return referenced_files

        # Execute the get_referenced_files in the main thread
        referenced_files = await (
            await Utils.wrapped_execute(action_query, get_referenced_files)
        )

        # Remove duplicates references
        referenced_files = list(set(referenced_files))

        # Each referenced file must be verified
        references_found: References = []

        # Check if the referenced files are reachable and prompt the user if not
        skip_all = False
        for attribute, file_path in referenced_files:
            if not is_valid_path(file_path) or not file_path.exists():
                # The value might be using a special pattern, we need to use findAllFilesForPattern
                file_sequence = ftpr.findAllFilesForPattern(str(file_path), None)
                if len(file_sequence) > 1:
                    file_path = [pathlib.Path(str(file)) for file in file_sequence][0]

            # Make sure the file path leads to a reachable file
            skip = False
            while not file_path.exists() or not file_path.is_absolute():
                if skip_all:
                    skip = True
                    break
                logger.warning(
                    "Could not reach the file %s at %s", file_path, attribute
                )
                file_path, skip, skip_all = await self._prompt_new_path(
                    action_query, file_path, attribute
                )
                if skip or file_path is None or skip_all:
                    skip = True
                    break
            # The user can decide to skip the references that are not reachable
            if skip or file_path is None:
                logger.info("Skipping the reference at %s", attribute)
                continue

            # Skip the references that are already conformed
            if parameters["skip_conformed"] and is_valid_pipeline_path(file_path):
                continue

            # Skip the custom extensions provided
            if "".join(file_path.suffixes) in parameters["filters"]:
                continue

            sequence = None
            # Test in the main thread if the current attribute might point to a sequence
            is_possible_sequence = await Utils.wrapped_execute(
                action_query, self._test_possible_sequence, attribute
            )
            if await is_possible_sequence:
                # Look for a file sequence
                for file_sequence in fileseq.findSequencesOnDisk(str(file_path.parent)):
                    # Find the file sequence that correspond the to file we are looking for
                    sequence_list = [pathlib.Path(str(file)) for file in file_sequence]
                    if file_path in sequence_list and len(sequence_list) > 1:
                        sequence = file_sequence
                        file_path = sequence_list
                        break

            # Append to the verified path
            references_found.append((attribute, file_path))
            if sequence is None:
                logger.info("Referenced file(s) %s found at %s", file_path, attribute)
            else:
                logger.info("Referenced file(s) %s found at %s", sequence, attribute)

        # Display a message to the user to inform about all the references to conform
        current_scene = await Utils.wrapped_execute(
            action_query, cmds.file, q=True, sn=True
        )
        referenced_file_paths = [
            fileseq.findSequencesInList(reference[1])
            if isinstance(reference[1], list)
            else [reference[1]]
            for reference in references_found
        ]
        message = f"The scene\n{await current_scene}\nis referencing non conformed file(s) :\n\n"
        for file_path in referenced_file_paths:
            message += f"- {' '.join([str(f) for f in file_path])}\n"

        message += "\nThese files must be conformed and repathed first. Press continue to conform and repath them"
        info_parameter = ParameterBuffer(
            type=TextParameterMeta("info"),
            name="info",
            label="Info",
            value=message,
        )
        # Send the message to the user
        if referenced_file_paths:
            await self.prompt_user(action_query, {"info": info_parameter})

        return {
            "attributes": [ref[0] for ref in references_found],
            "file_paths": [ref[1] for ref in references_found],
        }

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        new_path_parameter = self.command_buffer.parameters.get("new_path")
        skip_parameter = self.command_buffer.parameters.get("skip")
        skip_all_parameter = self.command_buffer.parameters.get("skip_all")
        if (
            new_path_parameter is not None
            and skip_parameter is not None
            and skip_all_parameter is not None
        ):
            if not skip_all_parameter.hide:
                skip_parameter.hide = parameters.get("skip_all", True)
                new_path_parameter.hide = parameters.get("skip_all", True)
            if not skip_parameter.hide:
                new_path_parameter.hide = parameters.get("skip", True)
