from __future__ import annotations

import logging
import pathlib
import tempfile
import typing
import uuid
from typing import Any, Dict, Optional

from maya import cmds, mel
from silex_client.action.command_base import CommandBase
from silex_maya.utils.thread import execute_in_main_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class CapturePreview(CommandBase):
    """
    Capture the current viewport either as a playblast or a single frame
    """

    def create_thumbnail(self) -> Optional[str]:
        file_name = str(uuid.uuid4())

        # Create temp path
        tmp_path = (pathlib.Path(tempfile.gettempdir()) / file_name).as_posix()

        current_frame = int(cmds.currentTime(query=True))

        # Filter user cameras
        default_cameras = ["front", "persp", "side", "top"]
        scene_cameras = cmds.listCameras()
        non_default_cameras = list(set(scene_cameras) - set(default_cameras))

        preview_width = 1920
        preview_height = preview_width * 0.6

        if len(non_default_cameras):
            cmds.lookThru(non_default_cameras[0])

        mel.eval(
            f'playblast -format image -filename "{tmp_path}" -clearCache 1 -viewer 0 -frame {current_frame} -showOrnaments 0 -percent 50 -compression "jpg" -quality 70 -widthHeight {preview_width} {preview_height};'
        )

        return f"{tmp_path}.0000.jpg"

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Take a thumbnail of the current viewport
        return await execute_in_main_thread(self.create_thumbnail)
