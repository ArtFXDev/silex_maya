from __future__ import annotations
from genericpath import exists
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger
from silex_maya.utils.utils import Utils
from silex_client.action.parameter_buffer import ParameterBuffer


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import maya.cmds as cmds
import os
import pathlib
import gazu

class ExportOBJ(CommandBase):
    """
    Export selection as obj
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
        "root_name": {"label": "Out Object Name", "type": str, "value": "", "hide": False }
    }

    async def _prompt_label_parameter(self, action_query: ActionQuery) -> pathlib.Path:
        """
        Helper to prompt the user a label
        """
        # Create a new parameter to prompt label

        label_parameter = ParameterBuffer(
            type=str,
            name="label_parameter",
            label="Could not export the selection: Select only one mesh component."
        )

        # Prompt the user with a label
        label = await self.prompt_user(
            action_query,
            { "label": label_parameter }
        )

        return label["label"]

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        # get selected objects
        def selected_objects():
            # get current selection 
            selected = cmds.ls(sl=True,long=True) or []
            selected.sort(key=len, reverse=True) # reverse
            return selected

        def export_obj(export_path):
            cmds.file(export_path, exportSelected=True, pr=True, type="OBJexport")

        # Get the output path
        directory = parameters.get("file_dir")
        file_name = parameters.get("file_name")
        root_name = parameters.get("root_name")
        
        # authorized type
        authorized_types = ["mesh", "transform"]    

        # get selected object
        selected = await Utils.wrapped_execute(action_query, lambda: selected_objects())
        selected = await selected # because first 'selected' is futur
        # exclude unauthorized type       
        selected = [item for item in selected if cmds.objectType(item.split("|")[-1]) in authorized_types]
        
        while len(selected) != 1:
            await self._prompt_label_parameter(action_query)
            # get selected object
            selected = await Utils.wrapped_execute(action_query, lambda: selected_objects())
            selected = await selected # because first 'selected' is futur      
            selected = [item for item in selected if cmds.objectType(item.split("|")[-1]) in authorized_types]

        # Export the selection in OBJ
        os.makedirs(directory, exist_ok=True)
         
        # compute path
        export_path = directory / f"{file_name}_{root_name}" if root_name else directory / f"{file_name}"
        extension = await gazu.files.get_output_type_by_name("obj")
        export_path = export_path.with_suffix(f".{extension['short_name']}")

        # Exec export
        await Utils.wrapped_execute(action_query, export_obj, export_path)

        return str(export_path)
