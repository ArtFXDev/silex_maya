from __future__ import annotations
from sys import path_importer_cache
from types import coroutine
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.command import CommandBuilder
from silex_client.utils.parameter_types import  MultipleSelectParameterMeta
from silex_maya.utils import thread as thread_maya 
from silex_client.utils import thread as thread_client 


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils import utils

from maya import cmds
import gazu.files
import fileseq
import subprocess
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
            "hide": True
        },
        "file_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": None,
            "hide": True
        },
        "frame_range": {
            "label": "Frame range (start, end, step)",
            "type": fileseq.FrameSet,
            "value": "1-50x1",
        },
        "render_layers": {
            "label": "Select render layers",
            "type": MultipleSelectParameterMeta,
            "value": ['defaultRenderLayer'],
        },
   
    }


    def _export_sequence(self,logger, path: pathlib.Path, frame_range: fileseq.FrameSet, render_layers: List[str], render_scene: pathlib.Path):
        """Export ass for each frame and each render layers"""

        # Set export rule for maya 
        cmds.workspace(fileRule=['ASS', path.parents[0]])

        frames_list = list(frame_range)
        render_layers_dirs: List[pathlib.Path] = list()

        # Export each render layers separetly
        for layer in render_layers:
            
            # Create layer folder ( in temporary dict )
            layer_dir: pathlib.Path = path.parents[0] / layer
            os.makedirs(layer_dir, exist_ok=True)

            # Each render layer is exported to a different directory
            render_layer_path = path.parents[0] / layer / f'{path.stem}_{layer}'
            ass_files = list(fileseq.FileSequence(f"{render_layer_path}.{frame_range}#{path.suffix}", pad_style=fileseq.PAD_STYLE_HASH4))

            # Each ass file conresponds to a frame
            frame_to_ass_dict = dict(zip(frames_list, ass_files))

            # Export sequence
            for frame in frame_to_ass_dict:

                batch_cmd = (
                    CommandBuilder("C:/Maya2022/Maya2022/bin/Render.exe", delimiter=None)
                    .param("r", "arnold")
                    .param("rl", layer)
                    .param("exportFileName", str(frame_to_ass_dict[frame]))
                    .param("noRender")
                )

                batch_cmd.set_last_param(str(render_scene))
                logger.error(batch_cmd)

                subprocess.call(batch_cmd.as_argv(), shell=True)

            render_layers_dirs.append(layer_dir)
        
        return render_layers_dirs

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        file_name: pathlib.Path = parameters["file_name"]
        directory: pathlib.Path = parameters["directory"] / file_name  # The directory parameter is temp directory
        extension: Dict[str, str] = (await gazu.files.get_output_type_by_name("ass"))['short_name']
        output_path = (directory / file_name).with_suffix(f'.{extension}')

        render_layers: List[str] = parameters['render_layers']
        frame_range: fileseq.FrameSet = parameters['frame_range']

        # Export to a ass sequence for each frame (in the awsome, brand new temporary directory)
        render_scene = pathlib.Path(await thread_maya.execute_in_main_thread(cmds.file, q=True, sn=True))
        render_layers_dirs: List[pathlib.Path] = await thread_client.execute_in_thread(self._export_sequence,logger, output_path, frame_range, render_layers, render_scene)

        return render_layers_dirs


    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        # Add render layers to parameters
        render_layers: List[str] = await thread_maya.execute_in_main_thread(cmds.ls, typ='renderLayer')
        self.command_buffer.parameters["render_layers"].type = MultipleSelectParameterMeta(*render_layers)

       
# from __future__ import annotations
# import typing
# from typing import Any, Dict, List

# from silex_client.action.command_base import CommandBase
# from silex_client.utils.parameter_types import SelectParameterMeta

# # Forward references
# if typing.TYPE_CHECKING:
#     from silex_client.action.action_query import ActionQuery

# from silex_maya.utils import utils

# from maya import cmds
# import gazu.files
# from fileseq import FrameSet
# import os
# import pathlib
# import logging

# class ExportAss(CommandBase):
#     """
#     Export selection as ass
#     """

#     parameters = {
#         "directory": {
#             "label": "File directory",
#             "type": pathlib.Path,
#             "value": None,
#         },
#         "file_name": {
#             "label": "File name",
#             "type": pathlib.Path,
#             "value": None,
#         },
#         "frame_range": {
#             "label": "Frame range (start, end, step)",
#             "type": FrameSet,
#             "value": "1-50x1",
#         },
#         "camera": {
#             "label": "Export camera",
#             "type": str,
#             "tooltip": "Name the render camera"
#         },
#         "selection": {
#             "label": "Export selection",
#             "type": bool,
#             "value": False,
#         },
#         "compression": {
#             "label": "Compression (gzip)",
#             "type": bool,
#             "value": False,
#         },
#         "bounding_box": {
#             "label": "Export Bounding Box",
#             "type": bool,
#             "value": True,
#         },
#         "binary_encoding": {
#             "label": "Use Binary Encoding",
#             "type": bool,
#             "value": True,
#         },
#         "options": {
#             "label": "Options",
#             "type": bool,
#             "value": True,
#         },
#         "lights_and_shadow": {
#             "label": "Lights",
#             "type": bool,
#             "value": True,
#         },
#         "shapes": {
#             "label": "shapes",
#             "type": bool,
#             "value": True,
#         },
#         "shaders": {
#             "label": "Shaders",
#             "type": bool,
#             "value": True,
#         },
#         "override": {
#             "label": "Override Nodes",
#             "type": bool,
#             "value": True,
#         },
#         "diver": {
#             "label": "Divers",
#             "type": bool,
#             "value": True,
#         },
#         "filters": {
#             "label": "Filters",
#             "type": bool,
#             "value": True,
#         },
#     }

#     def compute_mask(self, options: bool, camera: bool, light: bool, shape: bool, shader: bool, override: bool, diver: bool, filters: bool) -> int:
#         """Compute arnold mask from parameters"""

#         return 1*options + 2*camera + 4*light + 8*shape + \
#             16*shader + 32*override + 64*diver + 128*filters

#     def format_to_4_digits(self, frame: int) -> str:
#         """Format frame number to 4 digits"""

#         frame4: str = str(frame)
#         while len(frame4) < 4:
#             frame4 += "0" + frame4
        
#         return frame4

#     def export_sequence(self, path: pathlib.Path, extension: str, frame_range: List[int], cam: str, sel: List[str], Llinks: bool, Slinks: bool, Bbox: bool, binary: str, mask: int) -> List[str]:
#         """Export ass for each frame"""

#         # Set export rule for maya 
#         cmds.workspace(fileRule=['ASS', path.parents[0]])

#         exported_ass = list()

#         ## Loop for end and
#         for frame in frame_range:
#             exported_ass.append(f"{path}.{self.format_to_4_digits(frame)}.{extension}")
#             cmds.arnoldExportAss(
#                 f=path,
#                 cam=cam,
#                 sf=frame,
#                 ef=frame,
#                 s=sel,
#                 lightLinks=Llinks,
#                 shadowLinks=Slinks,
#                 boundingBox=Bbox,
#                 asciiAss=bool(1-binary),
#                 mask=mask,
#             )
            
#         return exported_ass

#     @CommandBase.conform_command()
#     async def __call__(
#         self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
#     ):
#         file_name: pathlib.Path = parameters["file_name"]
#         directory: pathlib.Path = parameters["directory"] / file_name  # Directory parameter is temp directory
               
#         frame_range: FrameSet = parameters['frame_range']

#         sel: str = parameters['selection']
#         Llinks: bool = parameters['lights_and_shadow']
#         Slinks: bool = parameters['lights_and_shadow']
#         Bbox: bool = parameters['bounding_box']
#         cam: str = parameters['camera']
#         binary: bool = parameters["binary_encoding"]

#         options: bool = parameters['options']
#         camera: bool = bool(parameters['camera'] != 'No camera')
#         light: bool = parameters['lights_and_shadow']
#         shape: bool = parameters['shapes']
#         shader: bool = parameters['shaders']
#         override: bool = parameters['override']
#         diver: bool = parameters['diver']
#         filters: bool = parameters['filters']
        
#         # Compute mask
#         mask: int = self.compute_mask(options, camera, light, shape, shader, override, diver, filters)

#         # Create export path
#         export_path_without_extention: pathlib.Path = directory / file_name

#         # Export the selection as ass sequence (in temp directory)
#         os.makedirs(directory, exist_ok=True)
#         frame_list: List[int] = list(FrameSet(frame_range))
#         extension: str = await gazu.files.get_output_type_by_name("ass")
#         exported_ass: Future = await utils.wrapped_execute(action_query, self.export_sequence, export_path_without_extention, extension['short_name'], frame_list, cam, sel, Llinks, Slinks, Bbox, binary, mask)
#         exported_ass: List[str] = await exported_ass

#         # look form missing ass
#         missing_ass: List[int] = list()
#         for ass in exported_ass:

#             if not os.path.exists(ass):
#                 missing_ass.append(frame_list[exported_ass.index(ass)]) 
        
#         if len(missing_ass):
#             logger.error(f"An error occured while exporting to ASS -> Frames : {'; '.join(missing_ass)} were not exported")

#         return directory


#     async def setup(
#         self,
#         parameters: Dict[str, Any],
#         action_query: ActionQuery,
#         logger: logging.Logger,
#     ):

#         # Add existing cameras to the parameters list
#         cam_list = await utils.wrapped_execute(action_query, cmds.listCameras)
#         cam_list = cam_list.result()
#         cam_list.append('No camera')
      
#         self.command_buffer.parameters["camera"].type = SelectParameterMeta(*cam_list)
#         self.command_buffer.parameters["camera"].value = cam_list[0]
       
