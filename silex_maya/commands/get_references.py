from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List, Tuple

import fileseq
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.files import (
    find_sequence_from_path,
    is_valid_pipeline_path,
    is_valid_path,
    sequence_exists,
)
from silex_client.utils.parameter_types import ListParameterMeta, TextParameterMeta
from silex_maya.utils.thread import execute_in_main_thread
from silex_maya.utils.constants import MATCH_FILE_SEQUENCE

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import maya.app.general.fileTexturePathResolver as ftpr
from maya import cmds


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
        "included_extensions": {
            "label": "Included extensions",
            "type": ListParameterMeta(str),
            "value": [],
            "tooltip": "List of file extensions to accept",
            "hide": True,
        },
        "skip_existing_conformed_file": {
            "label": "Skip existing conformed file",
            "type": bool,
            "value": True,
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

    def _test_possible_sequence(self, attribute: str, file_path: pathlib.Path) -> bool:
        """
        For some references, we don't want to look for sequences
        """
        # Test the parameters for a file node
        if cmds.nodeType(attribute) == "file":
            node = ".".join(attribute.split(".")[:-1])
            if (
                cmds.getAttr(f"{node}.uvTilingMode") == 0
                and cmds.getAttr(f"{node}.useFrameExtension") != 1
            ):
                return False

        # Maya references cannot be references
        if file_path.suffix in [".ma", ".mb"]:
            return False

        return True

    def _get_scene_references(
        self, logger: logging.Logger
    ) -> List[Tuple[str, pathlib.Path]]:
        """
        List all the references in the current scene
        Return the reference node/attribute and the file path
        """
        cmds.filePathEditor(rf=True)
        referenced_files: List[Tuple[str, pathlib.Path]] = []

        # Get the referenced files from the file path editor
        for attribute in cmds.filePathEditor(q=True, lf="", ao=True) or []:
            try:
                # Skip the nodes that are from an other referenced scene
                if cmds.referenceQuery(attribute, isNodeReferenced=True):
                    continue
            except RuntimeError:
                logger.warning("Attribute %s is not queryable", attribute)
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

            # Skip references that have an empty file_path
            if len(file_path) == 0:
                continue

            referenced_files.append((attribute, pathlib.Path(file_path)))

        # Make sure to not have duplicates in the references
        return list(set(referenced_files))

    def _get_reference_sequence(self, file_path: pathlib.Path) -> fileseq.FileSequence:
        """
        Convert the reference's file path into a sequence
        The reference is not a sequence, the returned value will be a sequence of one item
        """
        # We need to get the real path first, expand the syntaxes like <UDIM> or <frame04>
        pattern_match: List[str] = ftpr.findAllFilesForPattern(str(file_path), None)
        if len(pattern_match) > 0:
            file_path = pathlib.Path(str(pattern_match[0]))
        elif not is_valid_path(str(file_path)):
            for regex in MATCH_FILE_SEQUENCE:
                match = regex.match(str(file_path))
                if match is None:
                    continue
                file_path = pathlib.Path(str(file_path).replace(match.group(1), "0"))

        return find_sequence_from_path(file_path)

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        excluded_extensions = parameters["excluded_extensions"]
        included_extensions = parameters["included_extensions"]
        skip_existing_conformed_file = parameters["skip_existing_conformed_file"]

        # Each referenced file must be verified
        references: List[Tuple[str, fileseq.FileSequence]] = []

        referenced_files = await execute_in_main_thread(
            self._get_scene_references, logger
        )
        logger.error(referenced_files)


        skip_all = False
        for attribute, file_path in referenced_files:
            # Get the sequence that correspond to the file path
            file_paths = fileseq.findSequencesInList([file_path])[0]
            if self._test_possible_sequence(attribute, file_path):
                file_paths = await execute_in_main_thread(
                    self._get_reference_sequence, file_path
                )

            # Skip the custom extensions provided
            if file_paths.extension() in excluded_extensions:
                logger.warning(
                    "Excluded attribute %s pointing to %s", attribute, file_path
                )
                continue

            if len(excluded_extensions) > 0 and file_paths.extension() not in included_extensions:
                logger.warning(
                    "Excluded attribute %s pointing to %s", attribute, file_path
                )
                continue

            # Make sure the file path leads to a reachable file
            skip = False
            while not sequence_exists(file_paths):
                if skip_all:
                    skip = True
                    break
                logger.warning(
                    "Could not reach the file(s) %s at %s", file_paths, attribute
                )
                file_path, skip, skip_all = await self._prompt_new_path(
                    action_query, file_path, attribute
                )
                if skip or file_path is None or skip_all:
                    break
                file_paths = await execute_in_main_thread(
                    self._get_reference_sequence, file_path
                )

            # The user can decide to skip the references that are not reachable
            if skip or file_path is None:
                logger.info("Skipping the reference at %s", attribute)
                continue

            # Skip the references that are already conformed
            if skip_existing_conformed_file and all(is_valid_pipeline_path(pathlib.Path(path)) for path in file_paths):
                continue

            # Append to the verified path
            references.append((attribute, file_paths))
            logger.info("Referenced file(s) %s found at %s", file_paths, attribute)

        # Display a message to the user to inform about all the references to conform
        current_scene = await execute_in_main_thread(cmds.file, q=True, sn=True)
        message = (
            f"The scene\n{current_scene}\nis referencing non conformed file(s) :\n\n"
        )

        for attribute, file_path in references:
            message += f"- {file_path}\n"

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

        reference_attributes = [ref[0] for ref in references]
        reference_file_paths = [
            list(pathlib.Path(str(path)) for path in file_paths[1])
            for file_paths in references
        ]

        logger.error(reference_file_paths)

        return {
            "attributes": reference_attributes,
            "file_paths": reference_file_paths,
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
