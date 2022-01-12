from __future__ import annotations
import typing
from typing import Any, Dict
import logging
from maya import cmds
from maya import mel  
import tempfile
import uuid

from typing import Optional
from silex_client.action.command_base import CommandBase
from silex_maya.utils.utils import Utils


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class CapturePreview(CommandBase):
    """
    Capture the current viewport either as a playblast or a single frame
    """
    
    
    def create_thumbnail(self) -> Optional[str]:
    
        # 6 name thumbnail
        file_name = str(uuid.uuid1())

        # export path
        tmp_path = str(tempfile.gettempdir()) + "\\{}".format(file_name)
        tmp_path = tmp_path.replace('\\', '/')

        # get current frame
        current_frame = int(cmds.currentTime(query=True))

        default = ["front", "persp", "side", "top"]
        cam_lst = cmds.listCameras()
        cam_lst = list(set(cam_lst) - set(default))

        width = 1080 or int(cmds.getAttr("defaultResolution.width"))
        height = 720 or int(cmds.getAttr("defaultResolution.height"))
        deviceAspectRatio = width / float(height)

        if len(cam_lst):
            cmds.lookThru(cam_lst[0])
            cmds.setAttr("defaultResolution.deviceAspectRatio", deviceAspectRatio)
            mel.eval(f'playblast  -format image -filename "{tmp_path}" -clearCache 1 -viewer 0 -frame 1 -showOrnaments 0 -percent 50 -compression "jpg" -quality 70 -widthHeight {width} {height};')
            return f"{tmp_path}.0000.jpg"

        cmds.setAttr("defaultResolution.deviceAspectRatio", deviceAspectRatio)
        mel.eval(f'playblast  -format image -filename "{tmp_path}" -clearCache 1 -viewer 0 -frame 1 -showOrnaments 0 -percent 50 -compression "jpg" -quality 70 -widthHeight {width} {height};')


        return f"{tmp_path}.0000.jpg"


    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        # Take a thumbnail of the current viewport
        thumbnail_future = await Utils.wrapped_execute(action_query, self.create_thumbnail)
        thumbnail = thumbnail_future.result()

        return thumbnail
