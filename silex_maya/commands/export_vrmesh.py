from __future__ import annotations

import copy
import logging
import pathlib
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import (
    SelectParameterMeta,
    TextParameterMeta
)
from silex_maya.utils.thread import execute_in_main_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from maya import cmds


class ExportVrmesh(CommandBase):
    """
    Export selection as vrmesh and create a proxy
    """

    parameters = {
        "info": {
            "label": "Info",
            "type": TextParameterMeta(color="info"),
            "value": "Select the nodes that you want to export"
        },
        "directory": {
            "type": pathlib.Path,
            "value": None,
        },
        "separate_export": {
            "type": bool,
            "value": False,
        },
        "file_name": {
            "label": "file name", 
            "type": str, 
            "value": None, 
            "hide": True
        },
        "create_proxy": {
            "label": "Create proxy",
            "type": bool,
            "value": True,
        },
        "load_type": {
            "label": "Load as",
            "type": SelectParameterMeta(
                **{"None": "1", "Bounding box": "2", "Preview": "3", "Full geometry": "4"}
            ),
            "value": "3",
        },
        "node_name": {
            "type": str,
            "value": "vray_proxy",
        },
    }

    @staticmethod
    def import_references():
        for selection in cmds.ls(sl=True):
            for node in cmds.listRelatives(selection, allDescendents=True):
                if cmds.referenceQuery(node, isNodeReferenced=True):
                    file_path = cmds.referenceQuery(node, f=True)
                    cmds.file(file_path, importReference=True)

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        directory: pathlib.Path = parameters["directory"]
        separate_export: bool = parameters["separate_export"]
        node_name: str = parameters["node_name"]
        file_name: str = parameters["file_name"]
        create_proxy: bool = parameters["create_proxy"]
        load_type: int = int(parameters["load_type"])

        output_paths = []

        export_options = {
            "dir": directory.as_posix(),
            "createProxyNode": create_proxy,
            "geomToLoad": load_type,
            "exportType": 1,
            "node": node_name,
            "newProxyNode": True,
            "previewFaces": 1000,
            "fname": f"{file_name}.vrmesh",
        }

        # The crayCreateProxy command works with the selection, a selection is required for it to work
        while not await execute_in_main_thread(cmds.ls, sl=True):
            info_parameter = copy.copy(self.command_buffer.parameters["info"])
            info_parameter.value = "No nodes are selected. Please select a node and press continue"
            await self.prompt_user(action_query, {"info": info_parameter})

        directory.mkdir(parents=True, exist_ok=True)
        logger.info("Using vrmesh options: %s", export_options)

        # We export every nodes separatly instead of using the exportType 2 feature
        # because vray puts every procy nodes that it creates at the root of the world
        # and we want to preserve the node graph
        if separate_export:
            selection = await execute_in_main_thread(cmds.ls, sl=True)
            for node in selection:
                cmds.select(node)

                if create_proxy:
                    await execute_in_main_thread(self.import_references)

                node_parent = cmds.listRelatives(node, parent=True)
                if node_parent:
                    await execute_in_main_thread(cmds.parent, node, world=True)

                export_options["node"] = f"{node}_proxy"
                export_options["fname"] = f"{file_name}_{node}.vrmesh"
                logger.info("Exporting node %s as %s", export_options["node"], export_options["fname"])
                await execute_in_main_thread(cmds.vrayCreateProxy, **export_options)
                if node_parent:
                    await execute_in_main_thread(cmds.parent, export_options["node"], node_parent[0])

                output_paths.append(directory / export_options["fname"])
        else:
            if create_proxy:
                await execute_in_main_thread(self.import_references)
            logger.info("Exporting full selection as %s", export_options["fname"])
            await execute_in_main_thread(cmds.vrayCreateProxy, **export_options)
            output_paths.append(directory / export_options["fname"])

        return output_paths

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        self.command_buffer.parameters["node_name"].hide = parameters.get(
            "separate_export", False
        ) or not parameters.get("create_proxy", False)
        self.command_buffer.parameters["load_type"].hide = not parameters.get(
            "create_proxy", False
        )
