from __future__ import annotations

import pathlib
import typing
import fileseq
import logging
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_maya.utils.utils import Utils
from silex_client.utils.parameter_types import IntArrayParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import maya.cmds as cmds
import pathlib



class ArnoldCommand(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    
    res_x: int = cmds.getAttr('defaultResolution.width')
    res_y: int = cmds.getAttr('defaultResolution.height')


    parameters = {
        "export_dir": {
            "label": "File directory",
            "type": str,
            "value": None,
        },
         "exoprt_name": {
            "label": "File name",
            "type": str,
            "value": None,
        },
        #  "extension": {
        #     "label": "File name",
        #     "type": str,
        # },
        # "scene_path": {
        #     "label": "Scene path",
        #     "type": pathlib.Path
        #     "value": scene_path
        # },
        # "frame_range": {
        #     "label": "Frame range",
        #     "type": fileseq.FrameSet,
        # },
        "frame_range": {
            "label": "Frame range (start, end, padding)",
            "type":  IntArrayParameterMeta(2),
            "value": [0, 10]
        },
        "reslution": {
            "label": "Resolution ( x, y )",
            "type": IntArrayParameterMeta(2),
            "value": [res_x, res_y]
        },
        "task_size": {
            "label": "Task size",
            "type": int,
            "value": 10,
        },
        "skip_existing": {
            "label": "Skip existing frames",
            "type": bool,
            "value": True
        }
    }

    def _chunks(self, lst: List[Any], n: int) -> List[Any]:
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.logger
    ):

        directory: str = parameters.get("export_dir")
        exoprt_name: str = parameters.get("exoprt_name")
        # extension:  str = parameters.get("extension")
        scene: str = await Utils.wrapped_execute(action_query, cmds.file, query=True, sceneName=True)
        # scene: pathlib.Path = parameters.get('scene_path')
        # frame_range: fileseq.FrameSet = parameters.get("frame_range")
        frame_range: List[int] = parameters.get("frame_range")
        reslution: List[int] = parameters.get("reslution")
        task_size: int = parameters.get("task_size")
        skip_existing: int =  int(parameters.get("skip_existing"))

        # Set maya render settings
        cmds.setAttr("defaultRenderGlobals.outFormatControl", 0)
        cmds.setAttr("defaultRenderGlobals.animation", 1)
        cmds.setAttr("defaultRenderGlobals.putFrameBeforeExt", 1)
        cmds.setAttr("defaultRenderGlobals.extensionPadding", 4)

        chunks: List[Any] = list(self._chunks(
            range(frame_range[0], frame_range[1] + 1), task_size))
        cmd_dict: Dict[str, str] = dict()

        ### TEMP ###
        ##############
        directory = directory.replace("D:", r"\\marvin\TEMP_5RN" )
        ##############

        arg_list: List[str] = [
            f"-rd {directory}",
            f"-im {exoprt_name}",
            f"-x {reslution[0]}",
            f"-y {reslution[1]}",
            scene.result()
        ]

        # create Commands
        for chunk in chunks:
            start: int = chunk[0] 
            end: int = chunk[-1]
            logger.info(f"Creating a new task with frames: {start} {end}")
            cmd: str = "rez env silex_maya -- Render -r arnold {0} {1} {2} {3} -s {5} -e {6} {4}".format(*(arg_list + [start, end]))
            cmd_dict[f"frames : {start} - {end}"] = cmd 

        logger.info(f"exprot to {directory}")

        return {
            "commands": cmd_dict,
            "file_name": scene
        }
