from __future__ import annotations
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import SelectParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.utils import Utils

import maya.cmds as cmds
from fileseq import FrameSet
import os
import pathlib
import logging

class ExportAss(CommandBase):
    """
    Export selection as ass
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
        "frame_range": {
            "label": "Frame range (start, end, step)",
            "type": FrameSet,
            "value": "1-50x1",
        },
        "camera": {
            "label": "Export camera",
            "type": str,
            "tooltip": "Name the render camera"
        },
        "selection": {
            "label": "Export selection",
            "type": bool,
            "value": False,
        },
        "compression": {
            "label": "Compression (gzip)",
            "type": bool,
            "value": False,
        },
        "bounding_box": {
            "label": "Export Bounding Box",
            "type": bool,
            "value": True,
        },
        "binary_encoding": {
            "label": "Use Binary Encoding",
            "type": bool,
            "value": True,
        },
        "options": {
            "label": "Options",
            "type": bool,
            "value": True,
        },
        "lights_and_shadow": {
            "label": "Lights",
            "type": bool,
            "value": True,
        },
        "shapes": {
            "label": "shapes",
            "type": bool,
            "value": True,
        },
        "shaders": {
            "label": "Shaders",
            "type": bool,
            "value": True,
        },
        "override": {
            "label": "Override Nodes",
            "type": bool,
            "value": True,
        },
        "diver": {
            "label": "Divers",
            "type": bool,
            "value": True,
        },
        "filters": {
            "label": "Filters",
            "type": bool,
            "value": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):

        def export_sequence(path: str, frame_range: List[str], cam: str, sel: List[str], Llinks: bool, Slinks: bool, Bbox: bool, binary: str, mask: int) -> List[str]:

            p = pathlib.Path(path)
            cmds.workspace(fileRule=['ASS', p.parents[0]])

            exported_ass = list()

            ## loop for end and
            for frame in frame_range:
                ass = f'{path}_{frame}.ass'
                exported_ass.append(path)
                cmds.arnoldExportAss(
                    f=ass,
                    cam=cam,
                    sf=frame,
                    ef=frame,
                    s=sel,
                    lightLinks=Llinks,
                    shadowLinks=Slinks,
                    boundingBox=Bbox,
                    asciiAss=bool(1-binary),
                    mask=mask,
                )
                
            return exported_ass

        def compute_mask() -> int:
            options: bool = parameters.get('options')
            camera: bool = bool(parameters.get('camera') != 'No camera')
            light: bool = parameters.get('lights_and_shadow')
            shape: bool = parameters.get('shapes')
            shader: bool = parameters.get('shaders')
            override: bool = parameters.get('override')
            diver: bool = parameters.get('diver')
            filters: bool = parameters.get('filters')

            return 1*options + 2*camera + 4*light + 8*shape + \
                16*shader + 32*override + 64*diver + 128*filters

        file_name: str = str(parameters.get("file_name"))
        directory: str = f'{str(parameters.get("file_dir"))}{os.path.sep}{file_name}'
        
        # Check for extension
        if "." in file_name:
            file_name = file_name.split('.')[0]
          
        export_path_without_ext: str = f"{directory}{os.path.sep}{file_name}"
        export_path = f'{export_path_without_ext}.ass'
        frame_range: FrameSet = parameters.get('frame_range')
        sel: str = parameters.get('selection')
        Llinks: bool = parameters.get('lights_and_shadow')
        Slinks: bool = parameters.get('lights_and_shadow')
        Bbox: bool = parameters.get('bounding_box')
        cam: str = parameters.get('camera')
        binary: bool = parameters.get('binary_encoding')
        mask: int = compute_mask()

        # Export the selection as ass sequence
        os.makedirs(directory, exist_ok=True)
        frame_list: List[str] = list(FrameSet(frame_range))
        logger.error(frame_list)
        logger.error(type(frame_list[0]))
        exported_ass = await Utils.wrapped_execute(action_query, lambda: export_sequence(export_path_without_ext, frame_list, cam, sel, Llinks, Slinks, Bbox, binary, mask))

        # Test if the export worked
        import time
        time.sleep(1)

        missing_ass: str = ''
        for ass in exported_ass:

            if not os.path.exists(ass):
                missing_ass += frame_list[exported_ass.index(ass)] + ' ; '

        if missing_ass != '':
            raise Exception(
                f"An error occured while exporting {export_path} to ASS")

        return directory


    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        
        cam_list = await Utils.wrapped_execute(action_query, cmds.listCameras)
        cam_list = cam_list.result()
        cam_list.append('No camera')
      
        self.command_buffer.parameters["camera"].type = SelectParameterMeta(*cam_list)
        self.command_buffer.parameters["camera"].value = cam_list[0]
       
