from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.utils import Utils

import maya.cmds as cmds
import os
import pathlib
import gazu

class ExportFBX(CommandBase):
    """
    Export selection as FBX
    """

    parameters = {
        "file_dir": {
            "label": "File directory",
            "type": pathlib.Path,
            "value": None,
        },
        "file_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": None,
        },
        "root_name": {"label": "Out Object Name", "type": str, "value": None, "hide": False }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        
        # Test if the user selected something
        def get_selection():
            return len(cmds.ls(sl=True))

        # get select objects
        def select_objects():
            # get current selection 
            selected = cmds.ls(sl=True,long=True) or []
            selected.sort(key=len, reverse=True) # reverse
            return selected

         # get select objects
        def export_fbx(export_path, object_list):
            cmds.select(object_list)
            cmds.file(export_path, es=True, pr=True, type="FBX export")



        # Get the output path
        directory: str = parameters.get("file_dir")
        file_name: str = parameters.get("file_name")
        root_name = parameters.get("root_name")
        
        # authorized type
        authorized_type = ["transform", "mesh", "camera"]        
       
        if not await Utils.wrapped_execute(action_query, get_selection):
            raise Exception(
                "Could not export the selection: No selection detected")

        # get selected objects
        selected = await Utils.wrapped_execute(action_query, lambda: select_objects())
        selected = await selected
        
        # Export the selection in OBJ
        os.makedirs(directory, exist_ok=True)

        # exclude unauthorized type        
        selected = [item for item in selected if cmds.objectType(item.split("|")[-1]) in authorized_type]

        # compute path
        export_path = directory / f"{file_name}_{root_name}"
        extension = await gazu.files.get_output_type_by_name("fbx")
        export_path = export_path.with_suffix(f".{extension['short_name']}")

        # Export obj to fbx
        await Utils.wrapped_execute(action_query, export_fbx, export_path, selected)

        return str(export_path)
