import maya.cmds as mc
import tempfile
import uuid

from typing import Optional


def create_thumbnail() -> Optional[str]:
    # 6 name thumbnail
    id = str(uuid.uuid1())
    file_name = "{}.jpg".format(id)

    # export path
    tmp_path = str(tempfile.gettempdir()) + "\\{}".format(file_name)

    # get current frame
    current_frame = int(mc.currentTime(query=True))

    default = ["front", "persp", "side", "top"]
    cam_lst = mc.listCameras()
    cam_lst = list(set(cam_lst) - set(default))

    if len(cam_lst):
        width = 1080 or int(mc.getAttr("defaultResolution.width"))
        height = 540 or int(mc.getAttr("defaultResolution.height"))
        deviceAspectRatio = width / float(height)
        mc.lookThru(cam_lst[0])
        mc.setAttr("defaultResolution.deviceAspectRatio", deviceAspectRatio)
        mc.playblast(
            cf=tmp_path, fo=True, fr=current_frame, fmt="image", w=width, h=height
        )
        return None

    width = 1080 or int(mc.getAttr("defaultResolution.width"))
    height = 540 or int(mc.getAttr("defaultResolution.height"))
    deviceAspectRatio = width / float(height)
    mc.setAttr("defaultResolution.deviceAspectRatio", deviceAspectRatio)
    mc.playblast(cf=tmp_path, fo=True, fr=current_frame, fmt="image", w=width, h=height)

    return tmp_path
