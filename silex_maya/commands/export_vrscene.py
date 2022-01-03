from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import TextParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.utils import Utils

import maya.cmds as cmds
import os
import pathlib
import logging

class ExportVrscene(CommandBase):
    """
    Export selection as v-ray scene
    """

    # set camera list
    cam_list = cmds.listCameras()
    cam_list.append('No camera')

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
    }


    async def _prompt_warning(
        self, action_query: ActionQuery, export_valid: bool
    ) -> bool:
        """
        Helper to prompt the user a label
        """
        # check if export is valid
        while not export_valid:
            # Create a new parameter to prompt label
            info_parameter = ParameterBuffer(
                type=TextParameterMeta('warning'),
                name="Info",
                label="Info",
            )
            bool_parameter = ParameterBuffer(
                type=bool,
                name="full_scene",
                label='Publish full scene',
                value=True
            )
            # Prompt the user with a label
            prompt: Dict[str, ANy] = await self.prompt_user(action_query, {"info": info_parameter, 'full_scene': bool_parameter})

            # get selected objects
            future: Any = await Utils.wrapped_execute(action_query, cmds.ls, sl=1)
            slection_list = await future

            if len(slection_list) or prompt['full_scene']:
                export_valid =  True     
        
            return prompt['full_scene']
            
       


    @ CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):

        directory: str = str(parameters["file_dir"])
        file_name: str = str(parameters["file_name"])
        full_scene: bool = False
        export_valid: bool =  False
        
        # Check for extension
        if "." in file_name:
            file_name = file_name.split('.')[0]
          
        export_path: str = f"{directory}{os.path.sep}{file_name}.vrscene"

        # Export the selection in vrscene
        os.makedirs(directory, exist_ok=True)

        future: Any = await Utils.wrapped_execute(action_query, cmds.ls, sl=1)
        slection_list: List[str] = await future

        if len(slection_list):
            export_valid =  True

        # check if export is valid
        full_scene = await self._prompt_warning(action_query, export_valid)
        
        # export 
        await Utils.wrapped_execute(action_query, cmds.file, export_path, options=True, force=True,
                                    pr=True, ea=not(full_scene), es=full_scene, typ="V-Ray Scene")

        if not os.path.exists(export_path):
            raise Exception(
                f"An error occured while exporting {export_path} to vrscene")
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

