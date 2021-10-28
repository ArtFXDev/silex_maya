from __future__ import annotations
import typing
from typing import Any, Dict

from silex_maya.utils.utils import Utils
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import RangeParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_maya.utils.dialogs import Dialogs
from silex_maya.utils.utils import Utils

import maya.cmds as cmds
import os
import pathlib


class Export_ass(CommandBase):
    """
    Export selection as obj
    """

    parameters = {
        "file_path": {
            "label": "File path",
            "type": pathlib.Path,
            "value": None,
        },
        "selection": {
            "label": "Export selection",
            "type": bool,
        },
        "compression": {
            "label": "Compression (gzip)",
            "type": bool,
        },
        "bounding_box": {
            "label": "Export Bounding Box",
            "type": bool,
        },
        "binary_encoding": {
            "label": "Use Binary Encoding",
            "type": bool,
        },

        "camera": {
            "label": "Export camera",
            "type": str,
            "value": "",
            "tooltip": "Name the render camera"
        },
        "options": {
            "label": "Options",
            "type": bool,
        },
        "light": {
            "label": "Lights",
            "type": bool,
        },
        "shapes": {
            "label": "shapes",
            "type": bool,
        },
        "shaders": {
            "label": "Shaders",
            "type": bool,
        },
        "override": {
            "label": "Override Nodes",
            "type": bool,
        },
        "diver": {
            "label": "Divers",
            "type": bool,
        },
        "filters": {
            "label": "Filters",
            "type": bool,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        def compute_mask():
            pass

        path = parameters.get('file_path')
        sel = parameters.get('selection')
        Llinks = parameters.get('light')
        Slinks = parameters.get('light')
        Bbox = parameters.get('bounding_box')
        cam = parameters.get('camera')
        mask = compute_mask()

        p = pathlib.path(path)
        cmds.workspace(fileRule=['ASS', p.parents[0]])

        cmds.arnoldExportAss(
            f=path,
            cam=cam,
            s=sel,
            lightLinks=Llinks,
            shadowLinks=Slinks,
            boundingBox=Bbox,
            mask=mask,
        )

        if os.path.exists(path):
            Dialogs.inform('Export SUCCEDE !')
        else:
            Dialogs.error('ERROR : Export FAILD !')
