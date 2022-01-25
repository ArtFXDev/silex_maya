from __future__ import annotations

import fileseq
import pathlib
import typing
import logging
from typing import Any, Dict, Tuple, List

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import TextParameterMeta, ListParameterMeta
from silex_client.utils.files import (
    is_valid_pipeline_path,
    find_sequence_from_path,
    sequence_exists,
)
from silex_maya.utils.thread import execute_in_main_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from maya import cmds
import maya.app.general.fileTexturePathResolver as ftpr


class GetReferences(CommandBase):
    """
    Find all the referenced files, including textures, scene references...
    """

    parameters = {
        "excluded_extensions": {
            "label": "Excluded extensions",
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
        When a reference is not reachable, this method can be used to prompt the user.
        The user can either choose a new path, skip the reference, or skip all unreachable references
        """
        # Create all the parameters for the prompt
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
        # Send the prompt with all the created parameters
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

    def _test_possible_sequence(self, attribute: str) -> bool:
        """
        For some references, we don't want to look for sequences
        """
        # Test the parameters for a file node
        if cmds.nodeType(attribute) == "file":
            node = ".".join(attribute.split(".")[:-1])
            if cmds.getAttr(f"{node}.uvTilingMode") == 0:
                return False
            if cmds.getAttr(f"{node}.useFrameExtension") != 1:
                return False

        return True

    def _get_scene_references(self) -> List[Tuple[str, pathlib.Path]]:
        """
        List all the references in the current scene
        Return the reference node/attribute and the file path
        """
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

        # Make sure to not have duplicates in the references
        return list(set(referenced_files))

    def _get_reference_sequence(self, file_path: pathlib.Path) -> fileseq.FileSequence:
        """
        Convert the reference's file path into a sequence
        The reference is not a sequence, the returned value will be a sequence of one item
        """
        pattern_match = ftpr.findAllFilesForPattern(str(file_path), None)
        if len(pattern_match) > 0:
            file_path = pattern_match[0]

        return find_sequence_from_path(file_path)

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        excluded_extensions = parameters["excluded_extensions"]

        # Each referenced file must be verified
        references: List[Tuple[str, fileseq.FileSequence]] = []
        referenced_files = await execute_in_main_thread(self._get_scene_references)

        skip_all = False
        for attribute, file_path in referenced_files:
            # Get the sequence that correspond to the file path
            file_paths = await execute_in_main_thread(
                self._get_reference_sequence, file_path
            )

            # Make sure the file path leads to a reachable file
            skip = False
            while not sequence_exists(file_paths) and not skip_all:
                logger.warning(
                    "Could not reach the file(s) %s at %s", file_paths, attribute
                )
                file_path, skip, skip_all = await self._prompt_new_path(
                    action_query, file_path, attribute
                )
                file_paths = await execute_in_main_thread(
                    self._get_reference_sequence, file_path
                )
                if skip or file_path is None or skip_all:
                    break
            # The user can decide to skip the references that are not reachable
            if skip or file_path is None or skip_all:
                logger.info("Skipping the reference at %s", attribute)
                continue

            # Skip the references that are already conformed
            if all(is_valid_pipeline_path(path) for path in file_paths):
                continue

            # Skip the custom extensions provided
            if file_paths.extension() in excluded_extensions:
                continue

            # Append to the verified path
            references.append((attribute, file_paths))
            logger.info("Referenced file(s) %s found at %s", file_paths, attribute)

        # Display a message to the user to inform about all the references to conform
        current_scene = await execute_in_main_thread(cmds.file, q=True, sn=True)
        message = (
            f"The scene\n{current_scene}\nis referencing non conformed file(s) :\n\n"
        )

        for _, file_path in references:
            message += f"- {' '.join([str(f) for f in file_path])}\n"

        message += "\nThese files must be conformed and repathed first. Press continue to conform and repath them"
        info_parameter = ParameterBuffer(
            type=TextParameterMeta("info"),
            name="info",
            label="Info",
            value=message,
        )
        # Send the message to inform the user
        if references:
            await self.prompt_user(action_query, {"info": info_parameter})

        return {
            "attributes": [ref[0] for ref in references],
            "file_paths": [pathlib.Path(str(ref[1])) for ref in references],
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
