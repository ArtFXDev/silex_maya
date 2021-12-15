from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import TextParameterMeta

from silex_maya.utils.utils import Utils

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import maya.cmds as cmds
import os
import pathlib
import logging

class ExportMa(CommandBase):
    """
    Export selection as ma
    """

    parameters = {
        "directory": {
            "label": "File directory",
            "type": pathlib.Path,
            "value": None,
        },
        "file_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": None,
        }
    }

    async def _prompt_select_parameter(
        self, action_query: ActionQuery
    ) -> bool:
        """
        Helper to prompt the user a label
        """
        # Create a new parameter to prompt label

        info_parameter = ParameterBuffer(
            type=TextParameterMeta('warning'),
            name="Info",
            label="Info",
            # value=f"WARNING: No selection detected -> Please selecte somthing or publish full scene",
        )
        bool_parameter = ParameterBuffer(
            type=bool,
            name="full_scene",
            label='Publish full scene',
            value=True
        )
        # Prompt the user with a label
        prompt: Dict[str, ANy] = await self.prompt_user(action_query, {"info": info_parameter, 'full_scene': bool_parameter})

        return prompt['full_scene']


    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):

       
        directory: str = str(parameters.get("directory"))
        file_name: str = str(parameters.get("file_name"))
        full_scene: bool = False
        export_valid: bool =  False
        
        # Check for extension
        if "." in file_name:
            file_name = file_name.split('.')[0]
          
        export_path: str = f"{directory}{os.path.sep}{file_name}.ma"

        logger.info('export')

        # Export the selection in ma
        future: Any = await Utils.wrapped_execute(action_query, cmds.ls, sl=1)
        slection_list: List[str] = await future

        if len(slection_list):
            export_valid =  True

        while not export_valid:
            full_scene = await self._prompt_select_parameter(action_query)
            future: Any = await Utils.wrapped_execute(action_query, cmds.ls, sl=1)
            slection_list = await future
            if len(slection_list) or full_scene:
                export_valid =  True

        os.makedirs(directory, exist_ok=True)
        cmds.file(export_path, ea=full_scene, exportSelected=not(full_scene), pr=True, typ="mayaAscii")

        # # Test if the export worked
        # import time
        # time.sleep(1)

        if not os.path.exists(export_path):
            raise Exception(
                f"An error occured while exporting {export_path} to ma")
        return export_path


    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        if 'info' in parameters:
            if parameters.get("full_scene", False):            
                self.command_buffer.parameters["info"].type = TextParameterMeta('warning')
                self.command_buffer.parameters["info"].value = "WARNING: No selection detected -> Please selecte somthing or publish full scene"
            else:
                self.command_buffer.parameters["info"].type = TextParameterMeta('info')
                self.command_buffer.parameters["info"].value = 'Select somthing to publish'

