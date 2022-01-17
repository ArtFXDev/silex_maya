from __future__ import annotations
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import SelectParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.utils import Utils

from maya import cmds
import gazu.files
from fileseq import FrameSet
import os
import pathlib
import logging

class ExportAss(CommandBase):
    """
    Export selection as ass
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

    def compute_mask(self, options: bool, camera: bool, light: bool, shape: bool, shader: bool, override: bool, diver: bool, filters: bool) -> int:
        """Compute arnold mask from parameters"""

        return 1*options + 2*camera + 4*light + 8*shape + \
            16*shader + 32*override + 64*diver + 128*filters

    def format_to_4_digits(self, frame: int) -> str:
        """Format frame number to 4 digits"""

        frame = str(frame)
        for i in range(4 - len(frame)):
            frame = "0" + frame
        
        return frame

    def export_sequence(self, path: pathlib.Path, extension: str, frame_range: List[int], cam: str, sel: List[str], Llinks: bool, Slinks: bool, Bbox: bool, binary: str, mask: int) -> List[str]:
        """Export ass for each frame"""

        # Set export rule for maya 
        cmds.workspace(fileRule=['ASS', path.parents[0]])

        exported_ass = list()

        ## Loop for end and
        for frame in frame_range:
            exported_ass.append(f"{path}.{self.format_to_4_digits(frame)}.{extension}")
            cmds.arnoldExportAss(
                f=path,
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

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        file_name: pathlib.Path = parameters["file_name"]
        directory: pathlib.Path = parameters["directory"] / file_name  # Directory parameter is temp directory
               
        frame_range: FrameSet = parameters['frame_range']

        sel: str = parameters['selection']
        Llinks: bool = parameters['lights_and_shadow']
        Slinks: bool = parameters['lights_and_shadow']
        Bbox: bool = parameters['bounding_box']
        cam: str = parameters['camera']
        binary: bool = parameters["binary_encoding"]

        options: bool = parameters['options']
        camera: bool = bool(parameters['camera'] != 'No camera')
        light: bool = parameters['lights_and_shadow']
        shape: bool = parameters['shapes']
        shader: bool = parameters['shaders']
        override: bool = parameters['override']
        diver: bool = parameters['diver']
        filters: bool = parameters['filters']
        
        # Compute mask
        mask: int = self.compute_mask(options, camera, light, shape, shader, override, diver, filters)

        # Create export path
        export_path_without_extention: pathlib.Path = directory / file_name

        # Export the selection as ass sequence (in temp directory)
        os.makedirs(directory, exist_ok=True)
        frame_list: List[int] = list(FrameSet(frame_range))
        extension: str = await gazu.files.get_output_type_by_name("ass")
        exported_ass: Future = await Utils.wrapped_execute(action_query, self.export_sequence, export_path_without_extention, extension['short_name'], frame_list, cam, sel, Llinks, Slinks, Bbox, binary, mask)
        exported_ass: List[str] = await exported_ass

        # look form missing ass
        missing_ass: List[int] = list()
        for ass in exported_ass:

            if not os.path.exists(ass):
                missing_ass.append(frame_list[exported_ass.index(ass)]) 
        
        if len(missing_ass):
            logger.error(f"An error occured while exporting to ASS -> Frames : {'; '.join(missing_ass)} were not exported")

        return directory


    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        # Add existing cameras to the parameters list
        cam_list = await Utils.wrapped_execute(action_query, cmds.listCameras)
        cam_list = cam_list.result()
        cam_list.append('No camera')
      
        self.command_buffer.parameters["camera"].type = SelectParameterMeta(*cam_list)
        self.command_buffer.parameters["camera"].value = cam_list[0]
       
